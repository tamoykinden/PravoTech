from bot_client import BackendClient


class BaseService:
    """Базовый класс для всех сервисов VK-бота."""

    def __init__(self, session: BackendClient):
        self.session = session
