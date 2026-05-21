from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Union

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


class BaseKeyboard(ABC):
    """Базовый класс для всех клавиатур."""

    @abstractmethod
    def get_markup(self) -> Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]:
        """Возвращает готовую клавиатуру."""

        pass


class BaseReplyKeyboard(BaseKeyboard):
    """Базовый класс для Reply-клавиатур."""

    def __init__(
        self,
        resize_keyboard: bool = True,
        input_field_placeholder: str | None = None,
    ):
        self.resize_keyboard = resize_keyboard
        self.input_field_placeholder = input_field_placeholder

    def _build_reply_markup(self, buttons: List[List[KeyboardButton]]) -> ReplyKeyboardMarkup:
        """Собирает Reply-клавиатуру из списка кнопок."""

        builder = ReplyKeyboardBuilder()

        for row in buttons:
            for button in row:
                builder.add(button)
            builder.adjust(len(row))

        return builder.as_markup(
            resize_keyboard=self.resize_keyboard,
            input_field_placeholder=self.input_field_placeholder,
        )


class BaseInlineKeyboard(BaseKeyboard):
    """Базовый класс для Inline-клавиатур."""

    def __init__(self, row_width: int = 2):
        self.row_width = row_width

    def _build_inline_markup(self, buttons: List[InlineKeyboardButton]) -> InlineKeyboardMarkup:
        """Собирает Inline-клавиатуру из списка кнопок."""
        builder = InlineKeyboardBuilder()

        for button in buttons:
            builder.add(button)

        builder.adjust(self.row_width)

        return builder.as_markup()
