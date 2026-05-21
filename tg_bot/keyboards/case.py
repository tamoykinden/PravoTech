from __future__ import annotations

from typing import List

from aiogram.types import InlineKeyboardButton

from database.models import Case, Document
from tg_bot.keyboards.base import BaseInlineKeyboard


class CasesListKeyboard(BaseInlineKeyboard):
    """Inline-клавиатура для списка всех кейсов."""

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
                    callback_data=f'case_{case.id}'
                )
            )
        return self._build_inline_markup(buttons)


class CaseDetailKeyboard(BaseInlineKeyboard):
    """Inline-клавиатура для деталей кейса (документы)."""

    def __init__(self, documents: List[Document], case_id: int, row_width: int = 2):
        super().__init__(row_width=row_width)
        self.documents = documents
        self.case_id = case_id

    def get_markup(self):
        """Возвращает готовую Inline-клавиатуру с документами."""
        buttons = []

        for doc in self.documents:
            buttons.append(
                InlineKeyboardButton(
                    text=f'📎 {doc.title}',
                    callback_data=f'doc_{doc.id}'
                )
            )

        buttons.append(
            InlineKeyboardButton(
                text='Назад к кейсам',
                callback_data='back_to_cases'
            )
        )

        return self._build_inline_markup(buttons)
