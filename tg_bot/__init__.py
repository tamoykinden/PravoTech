from tg_bot.core import BotCore
from tg_bot.handlers import (
    cases_router,
    categories_router,
    common_router,
    document_router,
    feedback_router,
    search_router,
)


def create_bot() -> BotCore:
    """
    Функция для создания и настройки бота.
    Собирает все компоненты вместе.

    Returns:
        BotCore: Готовый к запуску экземпляр бота
    """

    bot_core = BotCore()

    bot_core.register_handlers(common_router)
    bot_core.register_handlers(cases_router)
    bot_core.register_handlers(categories_router)
    bot_core.register_handlers(search_router)
    bot_core.register_handlers(feedback_router)
    bot_core.register_handlers(document_router)

    return bot_core
