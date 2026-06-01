from config import CallbackAction
from database.models import Case
from vk_bot.keyboards.base import BaseInlineKeyboard


class SearchCasesListKeyboard(BaseInlineKeyboard):
    """Inline-клавиатура для списка кейсов из поиска."""

    def __init__(self, cases: list[Case]):
        self.cases = cases

    def get_markup(self) -> str:
        buttons = [
            (
                case.title,
                BaseInlineKeyboard.make_payload(CallbackAction.CASE_SEARCH, id=case.id),
            )
            for case in self.cases
        ]
        return self._build_inline_markup(buttons)
