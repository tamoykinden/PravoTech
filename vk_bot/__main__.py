import sys

from vk_bot import create_bot


def main() -> None:
    """
    Основная функция запуска VK-бота.
    Обрабатывает ошибки и корректный выход.
    """

    try:
        bot = create_bot()
        bot.start()
    except KeyboardInterrupt:
        print('Бот VK остановлен пользователем')
    except Exception as e:
        print(f'Критическая ошибка: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
