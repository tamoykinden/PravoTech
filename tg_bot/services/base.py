from bot_client import BackendClient


class BaseService:
    """Базовый класс для всех сервисов."""

    def __init__(self, session: BackendClient):
        """
        Инициализация сервиса.

        Args:
            session: Клиент центрального backend.
        """

        self.session = session
