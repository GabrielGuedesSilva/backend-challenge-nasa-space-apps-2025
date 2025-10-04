from http import HTTPStatus
from typing import Generic, List, Type, TypeVar, Union
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.database.query import Query
from src.utils.exceptions_messages import ExceptionsMessages

ModelType = TypeVar('ModelType')
SchemaType = TypeVar('SchemaType', bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    def __init__(
        self, sessionmaker: async_sessionmaker, model: Type[ModelType]
    ):
        self.sessionmaker = sessionmaker
        self.model = model
        self.model_name = self.model.__name__

    async def create(self, schema: SchemaType) -> ModelType:
        async with self.sessionmaker() as session:
            db_model = self.model(**schema.model_dump())
            session.add(db_model)
            await session.commit()
            await session.refresh(db_model)
            return db_model

    async def find(self, query: Query) -> List[ModelType]:
        async with self.sessionmaker() as session:
            stmt = select(self.model).order_by(self.model.created_at.desc())

            filters = query.build_filters(self.model)
            for expr in filters:
                stmt = stmt.where(expr)

            if query.limit is not None:
                stmt = stmt.limit(query.limit)

            stmt = stmt.offset(query.offset)

            result = await session.execute(stmt)
            return result.scalars().all()

    async def find_by_id(self, id: UUID) -> Union[ModelType, None]:
        async with self.sessionmaker() as session:
            stmt = select(self.model).where(self.model.id == id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def find_one(self, query: Query) -> Union[ModelType, None]:
        async with self.sessionmaker() as session:
            stmt = select(self.model)

            filters = query.build_filters(self.model)
            for expr in filters:
                stmt = stmt.where(expr)

            result = await session.execute(stmt)
            return result.scalars().first()

    async def update(self, id: UUID, schema: SchemaType) -> ModelType:
        async with self.sessionmaker() as session:
            stmt = select(self.model).filter_by(id=id)
            result = await session.execute(stmt)
            db_model = result.scalars().first()

            if not db_model:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=ExceptionsMessages.ID_NOT_FOUND.format(
                        model=self.model_name
                    ),
                )

            for key, value in schema.model_dump(exclude_unset=True).items():
                setattr(db_model, key, value)

            await session.commit()
            await session.refresh(db_model)
            return db_model

    async def delete(self, id: UUID) -> bool:
        async with self.sessionmaker() as session:
            stmt = select(self.model).filter_by(id=id)
            result = await session.execute(stmt)
            db_model = result.scalars().first()

            if not db_model:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=ExceptionsMessages.ID_NOT_FOUND.format(
                        model=self.model_name
                    ),
                )

            await session.delete(db_model)
            await session.commit()
            return True

    async def check_exists(self, id: UUID) -> bool:
        async with self.sessionmaker() as session:
            stmt = select(self.model).filter_by(id=id)
            result = await session.execute(stmt)
            db_model = result.scalars().first()

            if db_model is not None:
                return True
            else:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=ExceptionsMessages.ID_NOT_FOUND.format(
                        model=self.model_name
                    ),
                )

    async def check_duplicity(
        self, schema: SchemaType, unique_fields: List[str]
    ) -> bool:
        filters = [
            getattr(self.model, field) == getattr(schema, field)
            for field in unique_fields
            if hasattr(schema, field)
        ]

        if not filters:
            return False

        async with self.sessionmaker() as session:
            stmt = select(self.model).filter(or_(*filters))
            result = await session.execute(stmt)
            existing_record = result.scalars().first()

            if existing_record:
                conflict_fields = [
                    f"{field}='{getattr(schema, field)}'"
                    for field in unique_fields
                    if hasattr(schema, field)
                    and getattr(existing_record, field)
                    == getattr(schema, field)
                ]
                raise HTTPException(
                    status_code=HTTPStatus.CONFLICT,
                    detail=ExceptionsMessages.already_exists(
                        self.model_name, conflict_fields
                    ),
                )
            return False
