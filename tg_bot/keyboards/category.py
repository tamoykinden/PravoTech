from __future__ import annotations

from typing import List

from aiogram.types import InlineKeyboardButton

from config import ButtonConfig
from database.models import Case, CaseCategory
from tg_bot.keyboards.base import BaseInlineKeyboard


class CategoriesKeyboard(BaseInlineKeyboard):
    """Inline-клавиатура для выбора категории."""

    def __init__(self, categories: List[CaseCategory], row_width: int = 2):
        super().__init__(row_width=row_width)
        self.categories = categories

    def get_markup(self):
        """Возвращает готовую Inline-клавиатуру с категориями."""

        buttons = []
        for category in self.categories:
            buttons.append(
                InlineKeyboardButton(
                    text=category.name,
                    callback_data=f'cat_{category.id}'
                )
            )
        return self._build_inline_markup(buttons)


class CasesByCategoryKeyboard(BaseInlineKeyboard):
    """Inline-клавиатура для выбора кейса из категории."""

    def __init__(self, cases: List[Case], category_id: int, row_width: int = 1):
        super().__init__(row_width=row_width)
        self.cases = cases
        self.category_id = category_id

    def get_markup(self):
        """Возвращает готовую Inline-клавиатуру с кейсами."""

        buttons = []
        for case in self.cases:
            buttons.append(
                InlineKeyboardButton(
                    text=case.title,
                    callback_data=f'case_{case.id}'
                )
            )
        buttons.append(
            InlineKeyboardButton(
                text=ButtonConfig.BACK_TO_CATEGORIES,
                callback_data='back_to_categories'
            )
        )
        return self._build_inline_markup(buttons)
