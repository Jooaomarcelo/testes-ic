"""Authentication services module."""

from pymongo.asynchronous.database import AsyncDatabase

from src.core.security.jwt import decode_jwt, sign_jwt
from src.core.security.password import get_password_hash, verify_password
from src.models.user import User, UserCreate
from src.repos import user_repo
from src.utils.app_error import AppError
from src.utils.date_now import get_utc_now


async def authenticate_user(
	email: str,
	password: str,
	db: AsyncDatabase,
):
	"""Authenticate a user and return a JWT token.

	:param email: User email
	:type email: str
	:param password: User password
	:type password: str
	:param db: Database connection
	:type db: AsyncDatabase
	:return: JWT authentication token
	:rtype: str
	:raises AppError: If credentials are invalid
	"""
	user = await user_repo.get_user_by_email(email, db)

	if not user or not verify_password(password, user["password"]):
		raise AppError(status_code=401, message="Invalid credentials")

	return sign_jwt({"id": str(user["_id"])})


async def get_current_user(token: str, db: AsyncDatabase):
	"""Get authenticated user data from token.

	:param token: JWT authentication token
	:type token: str
	:param db: Database connection
	:type db: AsyncDatabase
	:return: Authenticated user data
	:rtype: dict
	:raises AppError: If token is invalid or user not found
	"""
	token_data = decode_jwt(token)

	if not token_data:
		raise AppError(status_code=401, message="Token invalid or expired")

	print(token_data.model_dump())

	user_id = token_data.id

	if not user_id:
		raise AppError(status_code=401, message="Invalid token")

	user = await user_repo.get_user_by_id(user_id, db)
	if not user:
		raise AppError(status_code=401, message="User not found")

	return user


async def signup_user(user: UserCreate, db: AsyncDatabase):
	"""Create a new user in the system.

	:param user: User data to be created
	:type user: UserCreate
	:param db: Database connection
	:type db: AsyncDatabase
	:return: Created user data
	:rtype: dict
	:raises AppError: If email already exists or passwords don't match
	"""
	existing = await user_repo.get_user_by_email(user.email, db)

	if existing:
		raise AppError(status_code=400, message="An error occurred during signup")

	if user.password != user.confirmation_password:
		raise AppError(status_code=400, message="Passwords do not match")

	user_db = User(
		username=user.username,
		full_name=user.full_name,
		email=user.email,
		password=get_password_hash(user.password),
		role=user.role,
		created_at=get_utc_now(),
		updated_at=get_utc_now(),
	)

	created_user = await user_repo.create_user(user_db, db)

	return created_user
