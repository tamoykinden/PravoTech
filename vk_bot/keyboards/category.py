from __future__ import annotations

from typing import List

from config import ButtonConfig
from database.models import Case, CaseCategory
from vk_bot.keyboards.base import BaseInlineKeyboard, make_payload


class CategoriesKeyboard(BaseInlineKeyboard):
    """Inline-клавиатура для выбора категории."""

    def __init__(self, categories: List[CaseCategory], row_width: int = 2):
        self.categories = categories
        self.row_width = row_width

    def get_markup(self) -> str:
        buttons = [
            (category.name, make_payload('cat', id=category.id))
            for category in self.categories
        ]
        return self._build_inline_markup(buttons, row_width=self.row_width)


class CasesByCategoryKeyboard(BaseInlineKeyboard):
    """Inline-клавиатура для выбора кейса из категории."""

    def __init__(self, cases: List[Case], category_id: int, row_width: int = 1):
        self.cases = cases
        self.category_id = category_id
        self.row_width = row_width

    def get_markup(self) -> str:
        buttons = [
            (
                case.title,
                make_payload('case_cat', id=case.id, category_id=self.category_id),
            )
            for case in self.cases
        ]
        buttons.append(
            (ButtonConfig.BACK_TO_CATEGORIES, make_payload('back_to_categories'))
        )
        return self._build_inline_markup(buttons, row_width=self.row_width)
