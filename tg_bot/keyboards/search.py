from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.models import Case


class SearchCasesListKeyboard:
    """Inline-клавиатура для списка кейсов из поиска."""

    def __init__(self, cases: list[Case]):
        self.cases = cases

    def get_markup(self) -> InlineKeyboardMarkup:
        buttons = []
        for case in self.cases:
            buttons.append([
                InlineKeyboardButton(
                    text=case.title[:50],
                    callback_data=f'case_search_{case.id}'
                )
            ])
        return InlineKeyboardMarkup(inline_keyboard=buttons)