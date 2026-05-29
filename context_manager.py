"""Хранение истории диалога по chat_id в памяти."""

from typing import Literal

Role = Literal["user", "assistant", "system"]

# Максимум сообщений в истории (пары user/assistant)
MAX_MESSAGES = 6

# chat_id -> список {"role": ..., "content": ...}
_history: dict[int, list[dict[str, str]]] = {}


def add_message(chat_id: int, role: Role, content: str) -> None:
    """Добавить сообщение и обрезать историю до MAX_MESSAGES."""
    if chat_id not in _history:
        _history[chat_id] = []
    _history[chat_id].append({"role": role, "content": content})
    if len(_history[chat_id]) > MAX_MESSAGES:
        _history[chat_id] = _history[chat_id][-MAX_MESSAGES:]


def get_history(chat_id: int) -> list[dict[str, str]]:
    """Вернуть копию истории для chat_id."""
    return list(_history.get(chat_id, []))


def clear(chat_id: int) -> None:
    """Очистить историю диалога."""
    _history.pop(chat_id, None)
