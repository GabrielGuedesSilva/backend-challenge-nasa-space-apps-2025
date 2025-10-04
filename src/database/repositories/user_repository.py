from sqlalchemy.ext.asyncio import async_sessionmaker

from src.database.models.user import User
from src.database.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, sessionmaker: async_sessionmaker):
        super().__init__(sessionmaker, User)
