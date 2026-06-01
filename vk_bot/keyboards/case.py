from config import CallbackAction
from database.models import Case, Document
from vk_bot.keyboards.base import BaseInlineKeyboard


class CasesListKeyboard(BaseInlineKeyboard):
    """Inline-клавиатура для списка кейсов."""

    def __init__(self, cases: list[Case]):
        self.cases = cases

    def get_markup(self) -> str:
        buttons = [
            (case.title, BaseInlineKeyboard.make_payload(CallbackAction.CASE_LIST, id=case.id))
            for case in self.cases
        ]
        return self._build_inline_markup(buttons)


class CaseDetailKeyboard(BaseInlineKeyboard):
    """Inline-клавиатура для деталей кейса (документы)."""

    def __init__(self, documents: list[Document], case_id: int):
        self.documents = documents
        self.case_id = case_id

    def get_markup(self) -> str:
        buttons = [
            (doc.title, BaseInlineKeyboard.make_payload(CallbackAction.DOCUMENT, id=doc.id))
            for doc in self.documents
        ]
        return self._build_inline_markup(buttons)
