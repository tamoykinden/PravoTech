from vkbottle import BaseStateGroup, GroupEventType
from vkbottle.bot import BotLabeler, Message, MessageEvent
from sqlalchemy.ext.asyncio import AsyncSession

from config import ButtonConfig, MessageConfig
from database.models import VKUser
from vk_bot.handlers.base import BaseHandlers
from vk_bot.handlers.helpers import action_rule, random_id
from vk_bot.keyboards.base import BaseInlineKeyboard, make_payload
from vk_bot.keyboards.main_menu import (
    MainMenuKeyboard,
    PDAgreementKeyboard,
    PDRetryKeyboard,
)


class CommonHandler(BaseHandlers):
    """Обработчик общих команд."""

    def __init__(self):
        self.labeler = BotLabeler()
        self._register()

    def _register(self) -> None:
        start_texts = ['/start', 'Начать', 'Старт', 'начать', 'старт']

        @self.labeler.private_message(text=start_texts)
        async def cmd_start(message: Message, user: VKUser, session: AsyncSession):
            if not user.pd_agreed:
                await self.send_message(
                    message,
                    MessageConfig.PD_AGREEMENT_TEXT,
                    PDAgreementKeyboard().get_markup(),
                )
                return

            await self.send_message(
                message,
                MessageConfig.START,
                MainMenuKeyboard().get_markup(),
            )

        @self.labeler.private_message(text=['/help', 'Помощь', 'помощь'])
        async def cmd_help(message: Message):
            await self.send_message(message, MessageConfig.HELP)

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            action_rule('pd_agree'),
        )
        async def pd_agree(
            event: MessageEvent,
            user: VKUser,
            session: AsyncSession,
        ):
            user.pd_agreed = True
            await session.commit()
            await event.send_empty_answer()
            await event.send_message(
                MessageConfig.START,
                keyboard=MainMenuKeyboard().get_markup(),
                random_id=random_id(),
            )

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            action_rule('pd_disagree'),
        )
        async def pd_disagree(event: MessageEvent):
            await event.send_empty_answer()
            await event.edit_message(
                MessageConfig.PD_DISAGREE_TEXT,
                keyboard=PDRetryKeyboard().get_markup(),
            )

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            action_rule('pd_retry'),
        )
        async def pd_retry(event: MessageEvent):
            await event.send_empty_answer()
            await event.edit_message(
                MessageConfig.PD_AGREEMENT_TEXT,
                keyboard=PDAgreementKeyboard().get_markup(),
            )

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            action_rule('back_to_main_menu'),
        )
        async def back_to_main_menu(event: MessageEvent, bot, state_dispenser):
            await state_dispenser.delete(event.peer_id)
            await event.send_empty_answer()
            await event.send_message(
                MessageConfig.BACK_TO_MAIN_MENU,
                keyboard=MainMenuKeyboard().get_markup(),
                random_id=random_id(),
            )


common_handler = CommonHandler()
common_router = common_handler.labeler
