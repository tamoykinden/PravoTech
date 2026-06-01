from config import ButtonConfig, CallbackAction
from database.models import Case, CaseCategory
from vk_bot.keyboards.base import BaseInlineKeyboard


class CategoriesKeyboard(BaseInlineKeyboard):
    """Inline-клавиатура для выбора категории."""

    def __init__(self, categories: list[CaseCategory]):
        self.categories = categories

    def get_markup(self) -> str:
        buttons = [
            (
                category.name,
                BaseInlineKeyboard.make_payload(CallbackAction.CATEGORY, id=category.id),
            )
            for category in self.categories
        ]
        return self._build_inline_markup(buttons)


class CasesByCategoryKeyboard(BaseInlineKeyboard):
    """Inline-клавиатура для выбора кейса из категории."""

    def __init__(self, cases: list[Case], category_id: int):
        self.cases = cases
        self.category_id = category_id

    def get_markup(self) -> str:
        buttons = [
            (
                case.title,
                BaseInlineKeyboard.make_payload(
                    CallbackAction.CASE_CAT,
                    id=case.id,
                    category_id=self.category_id,
                ),
            )
            for case in self.cases
        ]
        buttons.append((
            ButtonConfig.BACK_TO_CATEGORIES,
            BaseInlineKeyboard.make_payload(CallbackAction.BACK_TO_CATEGORIES),
        ))
        return self._build_inline_markup(buttons)
