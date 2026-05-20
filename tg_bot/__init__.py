from tg_bot.core import BotCore
from tg_bot.handlers.commands import commands_router
from tg_bot.handlers.course import course_router


def create_bot() -> BotCore:
    """
    Функция для создания и настройки бота.
    Собирает все компоненты вместе.

    Returns:
        BotCore: Готовый к запуску экземпляр бота
    """

    bot_core = BotCore()

    bot_core.register_handlers(commands_router)
    bot_core.register_handlers(course_router)

    return bot_core
