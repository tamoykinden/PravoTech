from __future__ import annotations

from typing import List

from aiogram.types import InlineKeyboardButton

from config import ButtonConfig
from database.models import Case, Document
from tg_bot.keyboards.base import BaseInlineKeyboard


class CasesListKeyboard(BaseInlineKeyboard):
    """Инлайн-клавиатура для списка всех кейсов."""

    def __init__(self, cases: List[Case], row_width: int = 1):
        super().__init__(row_width=row_width)
        self.cases = cases

    def get_markup(self):
        """Возвращает готовую Inline-клавиатуру со списком кейсов."""

        buttons = []
        for case in self.cases:
            buttons.append(
                InlineKeyboardButton(
                    text=case.title,
                    callback_data=f'case_list_{case.id}'
                )
            )
        return self._build_inline_markup(buttons)


class CaseDetailKeyboard(BaseInlineKeyboard):
    """Инлайн-клавиатура для деталей кейса (документы)."""

    def __init__(
        self,
        documents: List[Document],
        case_id: int,
        origin: str = 'all',
        row_width: int = 2,
    ):
        super().__init__(row_width=row_width)
        self.documents = documents
        self.case_id = case_id
        self.origin = origin

    def get_markup(self):
        """Возвращает готовую Inline-клавиатуру с документами."""

        buttons = []

        for doc in self.documents:
            buttons.append(
                InlineKeyboardButton(
                    text=doc.title,
                    callback_data=(
                        f'doc_{doc.id}_{self.case_id}_{self.origin}'
                    )
                )
            )
        return self._build_inline_markup(buttons)
