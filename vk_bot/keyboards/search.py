from __future__ import annotations

from typing import List

from database.models import Case
from vk_bot.keyboards.base import BaseInlineKeyboard, make_payload


class SearchCasesListKeyboard(BaseInlineKeyboard):
    """Inline-клавиатура для списка кейсов из поиска."""

    def __init__(self, cases: List[Case], row_width: int = 1):
        self.cases = cases
        self.row_width = row_width

    def get_markup(self) -> str:
        buttons = [
            (case.title, make_payload('case_search', id=case.id))
            for case in self.cases
        ]
        return self._build_inline_markup(buttons, row_width=self.row_width)
