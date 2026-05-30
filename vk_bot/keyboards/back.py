from config import ButtonConfig
from vk_bot.keyboards.base import BaseReplyKeyboard


class BackKeyboard(BaseReplyKeyboard):
    """Клавиатура с кнопкой «Назад»."""

    def get_markup(self) -> str:
        return self._build_reply_markup([[ButtonConfig.BACK]])
