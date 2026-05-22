from aiogram import F, Router, types
from aiogram.filters import Command

from config import MessageConfig
from tg_bot.handlers.base import BaseHandlers
from tg_bot.keyboards.main_menu import MainMenuKeyboard


class CommonHandler(BaseHandlers):
    """Обработчик общих команд."""

    def __init__(self):
        self.router = Router()
        self.router.message(Command('start'))(self.cmd_start)
        self.router.message(Command('help'))(self.cmd_help)

    async def cmd_start(self, message: types.Message):
        """Обработчик команды /start."""

        await message.answer(
            MessageConfig.START,
            reply_markup=MainMenuKeyboard().get_markup()
        )

    async def cmd_help(self, message: types.Message):
        """Обработчик команды /help."""

        await message.answer(MessageConfig.HELP)


common_handler = CommonHandler()
common_router = common_handler.router
