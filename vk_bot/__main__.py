import asyncio
import sys

from vk_bot import create_bot


async def main() -> None:
    """
    Основная асинхронная функция запуска VK-бота.
    Обрабатывает ошибки и корректный выход.
    """
    
    try:
        bot = create_bot()
        await bot.start()
    except KeyboardInterrupt:
        print('Бот VK остановлен пользователем')
    except Exception as e:
        print(f'Критическая ошибка: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
