from config import CallbackAction
from database.models import Case
from vk_bot.keyboards.base import BaseInlineKeyboard


class SearchCasesListKeyboard(BaseInlineKeyboard):
    """Inline-клавиатура для списка кейсов из поиска с пагинацией (по 3)."""

    def __init__(self, cases: list[Case], page: int = 0, per_page: int = 3):
        self.all_cases = cases
        self.page = page
        self.per_page = per_page

    def get_markup(self) -> str:
        start = self.page * self.per_page
        page_cases = self.all_cases[start:start + self.per_page]
        total_pages = (len(self.all_cases) + self.per_page - 1) // self.per_page

        buttons = [
            (
                case.title[:35],
                BaseInlineKeyboard.make_payload(CallbackAction.CASE_SEARCH, id=case.id),
            )
            for case in page_cases
        ]

        if total_pages > 1:
            next_page = self.page + 1 if self.page < total_pages - 1 else 0
            prev_page = self.page - 1 if self.page > 0 else total_pages - 1
            target = next_page if self.page < total_pages - 1 else prev_page
            nav_label = f'Стр. {self.page + 1}/{total_pages}'
            buttons.append((nav_label, BaseInlineKeyboard.make_payload('search_page', page=target)))

        return self._build_inline_markup(buttons)