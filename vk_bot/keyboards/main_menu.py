from config import ButtonConfig, CallbackAction
from vk_bot.keyboards.base import BaseInlineKeyboard, BaseReplyKeyboard


class MainMenuKeyboard(BaseReplyKeyboard):
    """Клавиатура главного меню."""

    def get_markup(self) -> str:
        buttons = [
            [ButtonConfig.CASES],
            [ButtonConfig.SEARCH, ButtonConfig.CATEGORIES],
            [ButtonConfig.FEEDBACK],
        ]
        return self._build_reply_markup(buttons, one_time=True)


class PDAgreementKeyboard(BaseInlineKeyboard):
    """Inline-клавиатура для согласия на обработку ПДн."""

    def get_markup(self) -> str:
        buttons = [
            (
                ButtonConfig.PD_DISAGREE_BUTTON,
                BaseInlineKeyboard.make_payload(CallbackAction.PD_DISAGREE),
            ),
            (
                ButtonConfig.PD_AGREE_BUTTON,
                BaseInlineKeyboard.make_payload(CallbackAction.PD_AGREE),
            ),
        ]
        return self._build_inline_markup(buttons, row_width=2)


class PDRetryKeyboard(BaseInlineKeyboard):
    """Inline-клавиатура для повторного запроса согласия."""

    def get_markup(self) -> str:
        buttons = [
            (
                ButtonConfig.PD_RETRY_BUTTON,
                BaseInlineKeyboard.make_payload(CallbackAction.PD_RETRY),
            ),
        ]
        return self._build_inline_markup(buttons)
