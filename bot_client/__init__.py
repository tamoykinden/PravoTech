"""Общий клиент backend для Telegram и VK."""

from bot_client.client import BackendClient, BackendError, RemoteUserCRUD

__all__ = ['BackendClient', 'BackendError', 'RemoteUserCRUD']
