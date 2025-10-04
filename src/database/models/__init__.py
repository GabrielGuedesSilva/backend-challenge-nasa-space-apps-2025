from sqlalchemy.ext.declarative import declarative_base

__all__ = ['Base', 'User']

Base = declarative_base()

from src.database.models.user import User
