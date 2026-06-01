from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from config import MessageConfig
from tg_bot.keyboards.main_menu import PDAgreementKeyboard

PD_CALLBACKS = frozenset({'pd_agree', 'pd_disagree', 'pd_retry'})


def is_pd_exempt(event: TelegramObject) -> bool:
    """События, доступные без согласия на обработку ПДн."""

    if isinstance(event, Message):
        if not event.text:
            return False
        text = event.text.strip()
        return text.startswith('/start') or text.startswith('/help')

    if isinstance(event, CallbackQuery):
        return event.data in PD_CALLBACKS

    return False


class PDAgreementMiddleware(BaseMiddleware):
    """Блокирует обработчики, если пользователь не дал согласие на ПДн."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get('user')
        if user is None or user.pd_agreed or is_pd_exempt(event):
            return await handler(event, data)

        keyboard = PDAgreementKeyboard().get_markup()

        if isinstance(event, Message):
            await event.answer(
                MessageConfig.PD_AGREEMENT_TEXT,
                reply_markup=keyboard,
            )
        elif isinstance(event, CallbackQuery):
            await event.answer(
                'Для использования бота необходимо согласие на обработку персональных данных.',
                show_alert=True,
            )
            await event.message.answer(
                MessageConfig.PD_AGREEMENT_TEXT,
                reply_markup=keyboard,
            )

        return None
