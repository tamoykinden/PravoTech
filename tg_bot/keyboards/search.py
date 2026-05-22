from __future__ import annotations

from typing import List

from aiogram.types import InlineKeyboardButton

from database.models import Case
from tg_bot.keyboards.base import BaseInlineKeyboard


class SearchCasesListKeyboard(BaseInlineKeyboard):
    """Инлайн-клавиатура для списка кейсов из поиска."""

    def __init__(self, cases: List[Case], row_width: int = 1):
        super().__init__(row_width=row_width)
        self.cases = cases

    def get_markup(self):
        buttons = []
        for case in self.cases:
            buttons.append(
                InlineKeyboardButton(
                    text=case.title,
                    callback_data=f'case_search_{case.id}'
                )
            )
        return self._build_inline_markup(buttons)
