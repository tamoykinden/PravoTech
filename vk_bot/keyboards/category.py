from config import CallbackAction
from database.models import Case, CaseCategory
from vk_bot.keyboards.base import BaseInlineKeyboard


class CategoriesKeyboard(BaseInlineKeyboard):
    """Inline-клавиатура для списка категорий."""

    def __init__(self, categories: list[CaseCategory]):
        self.categories = categories

    def get_markup(self) -> str:
        buttons = [
            (cat.name[:35], BaseInlineKeyboard.make_payload(CallbackAction.CATEGORY, id=cat.id))
            for cat in self.categories
        ]
        return self._build_inline_markup(buttons, row_width=2)


class CasesByCategoryKeyboard(BaseInlineKeyboard):
    """Inline-клавиатура для кейсов категории с пагинацией."""

    def __init__(
        self,
        cases: list[Case],
        category_id: int,
        page: int = 0,
        per_page: int = 6,
    ):
        self.cases = cases
        self.category_id = category_id
        self.page = page
        self.per_page = per_page

    def get_markup(self) -> str:
        total_pages = (
            len(self.cases) + self.per_page - 1
        ) // self.per_page
        safe_page = min(max(self.page, 0), max(total_pages - 1, 0))
        start = safe_page * self.per_page
        page_cases = self.cases[start:start + self.per_page]

        buttons = [
            (
                case.title[:35],
                BaseInlineKeyboard.make_payload(
                    CallbackAction.CASE_CAT,
                    id=case.id,
                    category_id=self.category_id,
                ),
            )
            for case in page_cases
        ]

        if total_pages > 1:
            next_page = (
                safe_page + 1
                if safe_page < total_pages - 1
                else 0
            )
            buttons.append((
                f'Стр. {safe_page + 1}/{total_pages} →',
                BaseInlineKeyboard.make_payload(
                    'category_case_page',
                    category_id=self.category_id,
                    page=next_page,
                ),
            ))

        return self._build_inline_markup(buttons, row_width=2)
