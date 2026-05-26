from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton

from config import ButtonConfig
from tg_bot.keyboards.base import BaseInlineKeyboard, BaseReplyKeyboard


class MainMenuKeyboard(BaseReplyKeyboard):
    """Клавиатура главного меню."""

    def get_markup(self):
        """Возвращает готовую клавиатуру главного меню."""

        buttons = [
            [KeyboardButton(text=ButtonConfig.CASES)],
            [
                KeyboardButton(text=ButtonConfig.SEARCH),
                KeyboardButton(text=ButtonConfig.CATEGORIES),
            ],
            [KeyboardButton(text=ButtonConfig.FEEDBACK)],
        ]

        return self._build_reply_markup(buttons)


class PDAgreementKeyboard(BaseInlineKeyboard):
    """Инлайн-клавиатура для согласия на обработку ПДн."""

    def get_markup(self) -> InlineKeyboardMarkup:
        buttons = [
            [InlineKeyboardButton(text=ButtonConfig.PD_AGREE_BUTTON, callback_data='pd_agree')],
            [InlineKeyboardButton(text=ButtonConfig.PD_DISAGREE_BUTTON, callback_data='pd_disagree')],
        ]
        return self._build_inline_markup(buttons)


class PDRetryKeyboard(BaseInlineKeyboard):
    """Инлайн-клавиатура для повторного запроса согласия."""

    def get_markup(self) -> InlineKeyboardMarkup:
        buttons = [
            [InlineKeyboardButton(text=ButtonConfig.PD_RETRY_BUTTON, callback_data='pd_retry')]
        ]
        return self._build_inline_markup(buttons)
