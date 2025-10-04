import pytest

from src.core.schemas.user_schemas import UserCreateSchema
from test.mocks.user import UserFactory


@pytest.mark.asyncio
async def test_create_user_by_service(user_service):
    data = UserFactory.build()
    new_user = UserCreateSchema(**data)

    user = await user_service.add(new_user)

    assert user.id is not None
    assert user.name == data['name']
    assert user.email == data['email']
    assert user.password == data['password']
