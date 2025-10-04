from http import HTTPStatus
from typing import List
from uuid import UUID

from fastapi import APIRouter, Request

from src.core.schemas.user_schemas import (
    UserCreateSchema,
    UserSchema,
    UserUpdateSchema,
)
from src.database.query import Query


class UserRouter:
    def __init__(self, container):
        self.user_service = container.user_service()
        self.router = APIRouter(
            prefix='/users',
            tags=['users'],
        )

        @self.router.post(
            '', status_code=HTTPStatus.CREATED, response_model=UserSchema
        )
        async def create_user(
            request: Request,
            user: UserCreateSchema,
        ):
            result = await self.user_service.add(user)
            return result

        @self.router.get(
            '', status_code=HTTPStatus.OK, response_model=List[UserSchema]
        )
        async def get_users(
            request: Request,
        ):
            query = Query(request.query_params)
            users = await self.user_service.get_all(query)
            return users

        @self.router.get(
            '/{user_id}', status_code=HTTPStatus.OK, response_model=UserSchema
        )
        async def get_user_by_id(
            request: Request,
            user_id: UUID,
        ):
            user = await self.user_service.get_by_id(user_id)
            return user

        @self.router.patch(
            '/{user_id}', status_code=HTTPStatus.OK, response_model=UserSchema
        )
        async def update_user(
            request: Request,
            user_id: UUID,
            user: UserUpdateSchema,
        ):
            updated_user = await self.user_service.update(user_id, user)
            return updated_user

        @self.router.delete('/{user_id}', status_code=HTTPStatus.NO_CONTENT)
        async def delete_user(
            request: Request,
            user_id: UUID,
        ):
            await self.user_service.remove(user_id)
