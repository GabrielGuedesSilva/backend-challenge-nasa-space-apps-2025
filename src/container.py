from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.services.user_service import UserService
from src.database.repositories.user_repository import UserRepository


class Container(containers.DeclarativeContainer):
    # Config
    config = providers.Configuration()

    # Engine
    engine = providers.Singleton(
        create_async_engine,
        config.DATABASE_URL,
    )

    # Async sessionmaker
    async_sessionmaker = providers.Singleton(
        async_sessionmaker,
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    # Repositories
    user_repository = providers.Factory(
        UserRepository, sessionmaker=async_sessionmaker
    )

    # Services
    user_service = providers.Factory(
        UserService, user_repository=user_repository
    )
