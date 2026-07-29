from sqlalchemy.ext.asyncio import AsyncSession
from vkbottle import GroupEventType
from vkbottle.bot import BotLabeler, Message, MessageEvent

from config import CallbackAction, MenuConfig, MessageConfig
from database.models import VKUser
from vk_bot.handlers.base import BaseHandlers
from vk_bot.keyboards.main_menu import (
    MainMenuKeyboard,
    PDAgreementKeyboard,
    PDRetryKeyboard,
)
from vk_bot.support.dispatch import VkDispatchSupport


class CommonHandler(BaseHandlers):
    """Обработчик общих команд."""

    def __init__(self):
        self.labeler = BotLabeler()
        self._register()

    def _register(self) -> None:
        @self.labeler.private_message(text=list(MenuConfig.START_TEXTS))
        async def cmd_start(
            message: Message,
            user: VKUser,
            session: AsyncSession,
            state_dispenser,
        ):
            await VkDispatchSupport.safe_delete_state(state_dispenser, message.peer_id)

            if not user.pd_agreed:
                await self.send_inline_message(
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

        @self.labeler.private_message(text=list(MenuConfig.HELP_TEXTS))
        async def cmd_help(message: Message):
            await self.send_message(message, MessageConfig.HELP)

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            VkDispatchSupport.action_rule(CallbackAction.PD_AGREE),
        )
        async def pd_agree(
            event: MessageEvent,
            user: VKUser,
            session: AsyncSession,
        ):
            user = await session.update_consent(user.id, True)
            await self.safe_answer_event(event)
            await self.safe_delete_event_message(event)
            await self.restore_main_menu(
                event.peer_id,
                event.ctx_api,
                MessageConfig.START,
            )

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            VkDispatchSupport.action_rule(CallbackAction.PD_DISAGREE),
        )
        async def pd_disagree(event: MessageEvent):
            await self.safe_answer_event(event)
            await event.edit_message(
                MessageConfig.PD_DISAGREE_TEXT,
                keyboard=PDRetryKeyboard().get_markup(),
            )

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            VkDispatchSupport.action_rule(CallbackAction.PD_RETRY),
        )
        async def pd_retry(event: MessageEvent):
            await self.safe_answer_event(event)
            await event.edit_message(
                MessageConfig.PD_AGREEMENT_TEXT,
                keyboard=PDAgreementKeyboard().get_markup(),
            )

        @self.labeler.raw_event(
            GroupEventType.MESSAGE_EVENT,
            MessageEvent,
            VkDispatchSupport.action_rule(CallbackAction.BACK_TO_MAIN_MENU),
        )
        async def back_to_main_menu(event: MessageEvent, state_dispenser):
            await VkDispatchSupport.safe_delete_state(state_dispenser, event.peer_id)
            await self.safe_answer_event(event)

            # Удаляем текущее сообщение (клавиатура «Выберите действие»)
            await self.safe_delete_event_message(event)
            # Удаляем предыдущее сообщение (файл)
            if event.conversation_message_id and event.conversation_message_id > 1:
                await self._delete_by_cmid(
                    event.ctx_api,
                    event.peer_id,
                    event.conversation_message_id - 1,
                )

            await self.restore_main_menu(
                event.peer_id,
                event.ctx_api,
                MessageConfig.BACK_TO_MAIN_MENU,
            )


common_handler = CommonHandler()
common_router = common_handler.labeler
