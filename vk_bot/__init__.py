from vk_bot.core import BotCore
from vk_bot.handlers import (
    common_router,
    cases_router,
    categories_router,
    search_router,
    feedback_router,
    document_router,
)


def create_bot() -> BotCore:
    """
    Функция для создания и настройки VK-бота.

    Регистрирует все роутеры в ядре бота.

    Returns:
        BotCore: Готовый к запуску экземпляр бота.
    """
    bot_core = BotCore()

    bot_core.register_handlers(common_router)
    bot_core.register_handlers(cases_router)
    bot_core.register_handlers(categories_router)
    bot_core.register_handlers(search_router)
    bot_core.register_handlers(feedback_router)
    bot_core.register_handlers(document_router)

    return bot_core
