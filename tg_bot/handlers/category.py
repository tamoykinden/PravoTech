from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from tg_bot.keyboards.back import BackKeyboard
from tg_bot.keyboards.category import CasesByCategoryKeyboard, CategoriesKeyboard
from tg_bot.services.case import CaseService
from tg_bot.services.category import CategoryService

router = Router()


@router.message(F.text == 'Категории')
async def show_categories(message: Message, session: AsyncSession):
    """Показать все категории."""

    service = CategoryService(session)
    categories = await service.get_all_categories()

    if not categories:
        await message.answer('Категории пока не добавлены.')
        return

    keyboard = CategoriesKeyboard(categories).get_markup()
    await message.answer(
        'Выберите категорию:',
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith('cat_'))
async def show_cases_by_category(callback: CallbackQuery, session: AsyncSession):
    """Показать кейсы из выбранной категории."""

    category_id = int(callback.data.split('_')[1])

    service = CaseService(session)
    cases = await service.get_cases_by_category(category_id)

    if not cases:
        await callback.message.edit_text(
            'В этой категории пока нет кейсов.',
            reply_markup=BackKeyboard().get_markup()
        )
        await callback.answer()
        return

    keyboard = CasesByCategoryKeyboard(cases, category_id).get_markup()
    await callback.message.edit_text(
        'Выберите кейс:',
        reply_markup=keyboard
    )
    await callback.answer()
