from __future__ import annotations

from typing import List

from config import ButtonConfig
from database.models import Case, Document
from vk_bot.keyboards.base import BaseInlineKeyboard, make_payload


class CasesListKeyboard(BaseInlineKeyboard):
    """Inline-клавиатура для списка кейсов."""

    def __init__(self, cases: List[Case], row_width: int = 1):
        self.cases = cases
        self.row_width = row_width

    def get_markup(self) -> str:
        buttons = [
            (case.title, make_payload('case_list', id=case.id))
            for case in self.cases
        ]
        return self._build_inline_markup(buttons, row_width=self.row_width)


class CaseDetailKeyboard(BaseInlineKeyboard):
    """Inline-клавиатура для деталей кейса (документы)."""

    def __init__(self, documents: List[Document], case_id: int, row_width: int = 2):
        self.documents = documents
        self.case_id = case_id
        self.row_width = row_width

    def get_markup(self) -> str:
        vk_documents = [doc for doc in self.documents if doc.vk_attachment]
        buttons = [
            (doc.title, make_payload('doc', id=doc.id))
            for doc in vk_documents
        ]
        return self._build_inline_markup(buttons, row_width=self.row_width)
