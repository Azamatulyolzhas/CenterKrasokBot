"""Логика запросов к OpenAI на основе базы знаний компании."""

from pathlib import Path

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    RateLimitError,
)

from context_manager import get_history

# Путь к файлу с данными компании (рядом с модулем)
COMPANY_INFO_PATH = Path(__file__).resolve().parent / "company_info.txt"

# Загружается при старте бота
_company_info: str = ""

# Шаблон системного промпта
SYSTEM_PROMPT_TEMPLATE = """Ты — AI-ассистент компании "Центр Красок".
Отвечай ТОЛЬКО на основе информации ниже. Не выдумывай.
Если информации нет в базе — скажи об этом и предложи связаться с менеджером.
Если вопрос не связан с компанией, её товарами или услугами — вежливо откажись отвечать по сути вопроса и укажи контакты компании из базы.

ИНФОРМАЦИЯ О КОМПАНИИ:
{company_info}"""


def load_company_info() -> str:
    """Загрузить company_info.txt при старте."""
    global _company_info
    if not COMPANY_INFO_PATH.exists():
        raise FileNotFoundError(f"Не найден файл: {COMPANY_INFO_PATH}")
    _company_info = COMPANY_INFO_PATH.read_text(encoding="utf-8").strip()
    return _company_info


def get_system_prompt() -> str:
    """Собрать системный промпт с актуальными данными компании."""
    if not _company_info:
        load_company_info()
    return SYSTEM_PROMPT_TEMPLATE.format(company_info=_company_info)


def get_fallback_message() -> str:
    """Сообщение при недоступности API — с контактами из базы."""
    if not _company_info:
        try:
            load_company_info()
        except FileNotFoundError:
            return (
                "Сейчас ассистент временно недоступен. "
                "Пожалуйста, свяжитесь с нами: https://centr-krasok.kz"
            )

    lines = [
        "Сейчас ассистент временно недоступен. Пожалуйста, свяжитесь с нами напрямую:",
        "",
    ]
    for raw_line in _company_info.splitlines():
        line = raw_line.strip()
        if line.startswith(("ТЕЛЕФОН:", "АДРЕС:", "САЙТ:", "ЧАСЫ РАБОТЫ:")):
            lines.append(line)
    if len(lines) <= 3:
        lines.append("Сайт: https://centr-krasok.kz")
    return "\n".join(lines)


async def get_ai_reply(
    client: AsyncOpenAI,
    model: str,
    chat_id: int,
    user_message: str,
) -> str:
    """
    Отправить запрос в OpenAI с системным промптом и историей диалога.
    Возвращает текст ответа или fallback при ошибке API.
    """
    messages: list[dict[str, str]] = [
        {"role": "system", "content": get_system_prompt()},
        *get_history(chat_id),
        {"role": "user", "content": user_message},
    ]

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=500,
        )
        return (response.choices[0].message.content or "").strip() or get_fallback_message()
    except (APIConnectionError, APIStatusError, RateLimitError, APITimeoutError, TimeoutError):
        return get_fallback_message()
