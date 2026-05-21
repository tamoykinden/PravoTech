from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from config import TextConfig
from tg_bot.keyboards.main_menu import MainMenuKeyboard

router = Router()


@router.message(Command('start'))
async def cmd_start(message: Message):
    await message.answer(
        TextConfig.START,
        reply_markup=MainMenuKeyboard().get_markup()
    )


@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer(TextConfig.HELP)
