import pytest


@pytest.fixture
def user_repository(container):
    return container.user_repository()
