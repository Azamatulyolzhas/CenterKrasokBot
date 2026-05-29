"""
Telegram-бот «Центр Красок» — чистый чат-интерфейс без команд и меню.
"""

import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatAction, ParseMode
from aiogram.types import Message
from dotenv import load_dotenv
from openai import AsyncOpenAI

from ai_handler import get_ai_reply, load_company_info
from context_manager import add_message, clear

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Минимальная длина сообщения пользователя
MIN_MESSAGE_LEN = 2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
openai_client: AsyncOpenAI | None = None


def validate_env() -> None:
    """Проверка обязательных переменных окружения."""
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if missing:
        logger.error("Не заданы переменные в .env: %s", ", ".join(missing))
        sys.exit(1)


@dp.message(F.text)
async def on_text(message: Message) -> None:
    """Обработка любого текстового сообщения (чистый чат, без меню)."""
    if not message.text or not message.chat.id:
        return

    text = message.text.strip()
    chat_id = message.chat.id

    # Первое открытие бота в Telegram (без меню и команд)
    if text.lower() in ("/start", "start"):
        clear(chat_id)
        await message.answer(
            "Здравствуйте! Я AI-ассистент компании <b>Центр Красок</b>.\n\n"
            "Задайте вопрос о наших товарах, услугах, доставке или контактах — "
            "отвечу на основе информации о компании.\n\n"
            "Сайт: <a href=\"https://centr-krasok.kz\">centr-krasok.kz</a>"
        )
        return

    # Слишком короткое сообщение
    if len(text) < MIN_MESSAGE_LEN:
        await message.answer(
            "Пожалуйста, уточните ваш вопрос — напишите чуть подробнее, "
            "чтобы я мог помочь."
        )
        return

    # Индикатор «печатает…»
    await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    # Периодически обновляем typing при долгом ответе
    typing_task = asyncio.create_task(_keep_typing(chat_id))

    try:
        reply = await get_ai_reply(
            client=openai_client,  # type: ignore[arg-type]
            model=OPENAI_MODEL,
            chat_id=chat_id,
            user_message=text,
        )
    finally:
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass

    # Сохраняем пару в историю после успешного ответа
    add_message(chat_id, "user", text)
    add_message(chat_id, "assistant", reply)

    await message.answer(reply)


async def _keep_typing(chat_id: int, interval: float = 4.0) -> None:
    """Поддерживать статус «печатает» пока идёт запрос к API."""
    while True:
        await asyncio.sleep(interval)
        await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)


async def main() -> None:
    validate_env()
    load_company_info()
    logger.info("База знаний компании загружена")

    global openai_client
    openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

    logger.info("Бот запущен (модель: %s)", OPENAI_MODEL)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
