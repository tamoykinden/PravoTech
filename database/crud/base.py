from typing import Any, List, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.base import Base

ModelType = TypeVar('ModelType', bound=Base)


class BaseCRUD:
    """Базовый CRUD класс, независимый от платформы."""

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        Инициализация CRUD.

        Args:
            model: Класс модели SQLAlchemy.
            session: Асинхронная сессия для работы с БД.
        """

        self.model = model
        self.session = session

    async def get_by_id(self, obj_id: int) -> Optional[ModelType]:
        """
        Получить объект по ID.

        Args:
            obj_id: ID объекта.

        Returns:
            Объект модели или None.
        """

        return await self.session.get(self.model, obj_id)

    async def get_all(self) -> List[ModelType]:
        """
        Получить все объекты модели.

        Returns:
            Список объектов.
        """

        result = await self.session.execute(select(self.model))

        return result.scalars().all()

    async def create(self, **kwargs: Any) -> ModelType:
        """
        Создать новый объект.

        Args:
            **kwargs: Поля модели.

        Returns:
            Созданный объект.
        """

        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj_id: int, **kwargs: Any) -> Optional[ModelType]:
        """
        Обновить объект по ID.

        Args:
            obj_id: ID объекта.
            **kwargs: Поля для обновления.

        Returns:
            Обновленный объект или None.
        """

        obj = await self.get_by_id(obj_id)
        if not obj:
            return None

        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)

        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj_id: int) -> bool:
        """
        Удалить объект по ID.

        Args:
            obj_id: ID объекта.

        Returns:
            True если удален, False если не найден.
        """
        
        obj = await self.get_by_id(obj_id)
        if not obj:
            return False

        await self.session.delete(obj)
        await self.session.commit()
        return True
