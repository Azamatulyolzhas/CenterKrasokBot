# Центр Красок — AI Telegram-бот

AI-ассистент для компании [Центр Красок](https://centr-krasok.kz) в Telegram. Бот отвечает на вопросы клиентов **только на основе** файла `company_info.txt` — без меню и команд, в формате обычного чата.

## Возможности

- Чистый чат-интерфейс (без кнопок и меню)
- Ответы на основе базы знаний компании
- Контекст диалога — последние 6 сообщений
- Индикатор «печатает…» во время запроса к ИИ
- При недоступности OpenAI — сообщение с контактами из базы
- Деплой на [Railway](https://railway.com) (long polling)

## Стек

- Python 3.11+
- [aiogram](https://docs.aiogram.dev/) 3
- [Groq API](https://console.groq.com)
- python-dotenv

## Структура проекта

```
├── bot.py              # Точка входа, Telegram polling
├── ai_handler.py       # Запросы к OpenAI, системный промпт
├── context_manager.py  # История диалога по chat_id
├── company_info.txt    # База знаний компании (редактируйте здесь)
├── requirements.txt
├── .env.example        # Шаблон переменных окружения
├── railway.toml        # Конфигурация деплоя Railway
├── Procfile
└── runtime.txt
```

## Быстрый старт (локально)

### 1. Клонирование и окружение

```powershell
cd "путь\к\AI Bot cenkras"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Переменные окружения

```powershell
copy .env.example .env
```

Заполните `.env`:

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен бота от [@BotFather](https://t.me/BotFather) |
| `OPENAI_API_KEY` | API-ключ Groq |

Опционально:

| Переменная | По умолчанию |
|------------|--------------|
| `OPENAI_MODEL` | `Groq` |

> **Важно:** файл `.env` не коммитьте в Git — он уже в `.gitignore`.

### 3. База знаний

Отредактируйте `company_info.txt` — адреса, телефоны, услуги, бренды, доставку. Бот использует **только** этот текст при ответах.

### 4. Запуск

```powershell
python bot.py
```

В логах должно появиться:

```
База знаний компании загружена
Бот запущен (модель: gpt-4o-mini)
```

Напишите боту в Telegram: `/start` или любой вопрос о компании.

## Поведение бота

| Ситуация | Действие бота |
|----------|----------------|
| `/start` | Приветствие, сброс истории диалога |
| Короткое сообщение (менее 2 символов) | Просьба уточнить вопрос |
| Вопрос по компании | Ответ из `company_info.txt` через GPT |
| Вопрос не по теме | Вежливый отказ + контакты |
| Ошибка OpenAI | Fallback с телефоном, адресом, сайтом |

Параметры ИИ: `temperature=0.3`, `max_tokens=500`, контекст — 6 последних сообщений.

## Деплой на Railway

### Подготовка

1. Аккаунт на [railway.com](https://railway.com)
2. Репозиторий на GitHub **или** [Railway CLI](https://docs.railway.com/develop/cli): `npm i -g @railway/cli`

### Через веб-интерфейс

1. **New Project** → **Deploy from GitHub repo** (выберите этот репозиторий).
2. **Variables** → добавьте:
   - `BOT_TOKEN`
   - `OPENAI_API_KEY`
3. **Settings** сервиса:
   - **Health Check** — **Disabled** (бот не поднимает HTTP-сервер)
   - **Replicas** — **1** (иначе конфликт polling одного токена)
4. Дождитесь успешного деплоя и проверьте **Deploy Logs**.

### Через CLI

```powershell
cd "путь\к\проекту"
railway login
railway init
railway variables set BOT_TOKEN=ваш_токен OPENAI_API_KEY=ваш_ключ
railway up
```

Команда запуска задана в `railway.toml`:

```toml
startCommand = "python bot.py"
```

### После деплоя

- Остановите локальный `python bot.py`, если он запущен — **один токен = один процесс**.
- Проверьте бота в Telegram.

## Обновление базы знаний

1. Измените `company_info.txt`
2. Локально: перезапустите `python bot.py`
3. На Railway: сделайте commit + push (или `railway up`) — файл уходит в деплой вместе с кодом

Переменные в Railway для `company_info.txt` не нужны.

## Устранение неполадок

| Проблема | Решение |
|----------|---------|
| `Не заданы переменные BOT_TOKEN` | Проверьте `.env` локально или **Variables** на Railway |
| `Conflict: terminated by other getUpdates` | Остановите второй экземпляр бота (локально или лишняя реплика на Railway) |
| Сервис на Railway постоянно перезапускается | Отключите Health Check |
| Бот молчит | Смотрите логи деплоя; проверьте `OPENAI_API_KEY` и баланс OpenAI |
| Бот «выдумывает» факты | Дополните `company_info.txt`; не повышайте `temperature` |

## Безопасность

- Не публикуйте `.env` и токены в репозитории
- Ограничьте доступ к репозиторию с `company_info.txt`, если там чувствительные данные
- Регулярно обновляйте зависимости: `pip install -U -r requirements.txt`

## Лицензия

Проект для внутреннего использования компании «Центр Красок».
