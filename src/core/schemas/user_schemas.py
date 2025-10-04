from datetime import datetime
from typing import Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from .types import UserName


class UserCreateSchema(BaseModel):
    name: UserName
    age: Optional[int] = None
    email: EmailStr
    password: str


class UserSchema(BaseModel):
    id: UUID
    name: UserName
    age: Union[int, None]
    email: EmailStr
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdateSchema(BaseModel):
    name: Optional[UserName] = None
    age: Optional[int] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
