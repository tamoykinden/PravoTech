from config import ButtonConfig
from vk_bot.keyboards.base import BaseInlineKeyboard, BaseReplyKeyboard, make_payload


class MainMenuKeyboard(BaseReplyKeyboard):
    """Клавиатура главного меню."""

    def get_markup(self) -> str:
        buttons = [
            [ButtonConfig.CASES],
            [ButtonConfig.SEARCH, ButtonConfig.CATEGORIES],
            [ButtonConfig.FEEDBACK],
        ]
        return self._build_reply_markup(buttons)


class PDAgreementKeyboard(BaseInlineKeyboard):
    """Inline-клавиатура для согласия на обработку ПДн."""

    def get_markup(self) -> str:
        buttons = [
            (ButtonConfig.PD_DISAGREE_BUTTON, make_payload('pd_disagree')),
            (ButtonConfig.PD_AGREE_BUTTON, make_payload('pd_agree')),
        ]
        return self._build_inline_markup(buttons, row_width=2)


class PDRetryKeyboard(BaseInlineKeyboard):
    """Inline-клавиатура для повторного запроса согласия."""

    def get_markup(self) -> str:
        buttons = [
            (ButtonConfig.PD_RETRY_BUTTON, make_payload('pd_retry')),
        ]
        return self._build_inline_markup(buttons)
