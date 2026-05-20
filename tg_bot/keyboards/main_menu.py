from __future__ import annotations

from aiogram.utils.keyboard import ReplyKeyboardBuilder

from tg_bot.keyboards.base import BaseReplyKeyboards


class MainMenuKeyboard(BaseReplyKeyboards):
    """Клавиатура главного меню."""

    def get_keyboard(self) -> ReplyKeyboardBuilder:
        """
        Возвращает билдер с кнопками главного меню.

        Returns:
            ReplyKeyboardBuilder: Билдер с добавленными кнопками.
        """

        builder = ReplyKeyboardBuilder()

        builder.button(text='Список кейсов')
        builder.button(text='Поиск кейса')
        builder.button(text='🗂Категории')
        builder.button(text='❤Обратная связь')

        builder.adjust(2, 2)  # ряды: 1 кнопка, 2 кнопки, 1 кнопка

        return builder

    def get_markup(self):
        """
        Возвращает готовую клавиатуру главного меню.

        Returns:
            ReplyKeyboardMarkup: Готовая клавиатура.
        """

        builder = self.get_keyboard()
        return self._as_markup(builder)


def get_main_menu():
    """Возвращает готовую клавиатуру главного меню."""

    return MainMenuKeyboard().get_markup()