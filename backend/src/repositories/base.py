"""
Base repository with common CRUD operations
"""
from typing import Any, Generic, Type, TypeVar
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.base import Base

ModelType = TypeVar("ModelType", bound=Base)

logger = structlog.get_logger(__name__)


class BaseRepository(Generic[ModelType]):
    """Base repository with common database operations"""
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
    
    async def get_by_id(self, id: UUID) -> ModelType | None:
        """Get entity by ID"""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> list[ModelType]:
        """Get all entities with pagination"""
        result = await self.session.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return list(result.scalars().all())
    
    async def create(self, **kwargs) -> ModelType:
        """Create new entity"""
        entity = self.model(**kwargs)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        
        logger.info(
            "entity_created",
            model=self.model.__name__,
            id=entity.id
        )
        
        return entity
    
    async def update(self, entity: ModelType, **kwargs) -> ModelType:
        """Update existing entity"""
        for key, value in kwargs.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        
        await self.session.flush()
        await self.session.refresh(entity)
        
        logger.info(
            "entity_updated",
            model=self.model.__name__,
            id=entity.id
        )
        
        return entity
    
    async def delete(self, entity: ModelType) -> None:
        """Delete entity"""
        entity_id = entity.id
        await self.session.delete(entity)
        await self.session.flush()
        
        logger.info(
            "entity_deleted",
            model=self.model.__name__,
            id=entity_id
        )
    
    async def commit(self) -> None:
        """Commit transaction"""
        await self.session.commit()
    
    async def rollback(self) -> None:
        """Rollback transaction"""
        await self.session.rollback()
