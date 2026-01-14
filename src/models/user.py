"""User models module."""

from datetime import datetime

from bson import ObjectId
from pydantic import ConfigDict, EmailStr, Field

from .base_model import CustomBaseModel, MongoBaseModel
from .enums import UserRole


class User(MongoBaseModel):
	"""User model stored in database."""

	username: str
	full_name: str
	email: EmailStr
	password: str
	role: UserRole


class UserCreate(CustomBaseModel):
	"""User creation model with password validation."""

	username: str
	full_name: str
	email: EmailStr
	role: UserRole | None = UserRole.USER
	# For 1 big letter, 1 number, 1 special char and min length 8: pattern="^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
	password: str = Field(min_length=8)
	confirmation_password: str = Field(min_length=8)


class UserIn(CustomBaseModel):
	"""User input data model for authentication."""

	email: EmailStr
	password: str


class UserOut(User):
	"""User output data model (without password)."""

	id: ObjectId | None = Field(default=None, alias="_id")

	username: str
	email: EmailStr
	full_name: str
	role: UserRole
	created_at: datetime
	updated_at: datetime

	model_config = ConfigDict(
		arbitrary_types_allowed=True,
	)


class UserUpdatePass(CustomBaseModel):
	"""Model for user password update."""

	id: ObjectId | None = Field(default=None, alias="_id")
	email: EmailStr | None

	old_password: str
	new_password: str = Field(min_length=8)
	confirmation_password: str = Field(min_length=8)

	model_config = ConfigDict(
		arbitrary_types_allowed=True,
	)
