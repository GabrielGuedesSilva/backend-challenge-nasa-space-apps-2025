import pytest


@pytest.fixture
def user_service(container):
    return container.user_service()
