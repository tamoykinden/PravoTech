from __future__ import annotations

from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


class BaseReplyKeyboards:
    """
    Базовый класс для всех reply-клавиатур бота.

    Предоставляет общий метод для формирования клавиатур с едиными настройками.
    Все классы клавиатур должны наследоваться от этого класса.
    """

    @staticmethod
    def _as_markup(
        builder: ReplyKeyboardBuilder,
        *,
        resize_keyboard: bool = True,
        input_field_placeholder: str | None = None,
    ) -> ReplyKeyboardMarkup:
        """
        Преобразует билдер в готовую клавиатуру.

        Args:
            builder: Билдер с добавленными кнопками.
            resize_keyboard: Автоматически изменять размер кнопок под экран.
            input_field_placeholder: Текст-подсказка в поле ввода.

        Returns:
            ReplyKeyboardMarkup: Готовая клавиатура.
        """

        return builder.as_markup(
            resize_keyboard=resize_keyboard,
            input_field_placeholder=input_field_placeholder,
        )
