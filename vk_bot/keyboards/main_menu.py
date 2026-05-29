import json

from config import ButtonConfig
from vk_bot.keyboards.base import BaseKeyboard


class MainMenuKeyboard(BaseKeyboard):
    """Клавиатура главного меню."""

    def get_markup(self) -> str:
        keyboard = {
            'one_time': False,
            'buttons': [
                [{'color': 'primary', 'action': {'type': 'text', 'label': ButtonConfig.CASES}}],
                [
                    {'color': 'secondary', 'action': {'type': 'text', 'label': ButtonConfig.SEARCH}},
                    {'color': 'secondary', 'action': {'type': 'text', 'label': ButtonConfig.CATEGORIES}}
                ],
                [{'color': 'primary', 'action': {'type': 'text', 'label': ButtonConfig.FEEDBACK}}]
            ]
        }
        return json.dumps(keyboard, ensure_ascii=False)
