from pymongo.asynchronous.database import AsyncDatabase

from src.core.security.password import get_password_hash, verify_password
from src.models.user import UserUpdatePass
from src.repos import user_repo
from src.utils.app_error import AppError


async def get_all_users(db: AsyncDatabase):
	"""Retrieves all users from the database.

	:param db: Database connection
	:type db: AsyncDatabase
	:return: List of all users
	:rtype: list[dict]
	"""
	users = await user_repo.get_users(db)
	return users


async def get_user_by_id(user_id: str, db: AsyncDatabase) -> dict:
	"""Retrieves a user by their ID.

	:param user_id: The ID of the user to retrieve
	:type user_id: str
	:param db: Database connection
	:type db: AsyncDatabase
	:return: The user data if found
	:rtype: dict
	:raises AppError: If user is not found
	"""
	user = await user_repo.get_user_by_id(user_id, db)

	if not user:
		raise AppError(status_code=404, message="User not found")

	return user


async def update_user_pass(user: UserUpdatePass, db: AsyncDatabase):
	"""Updates an user password in the system.

	:param user: User new password data
	:type user: UserUpdatePass
	:param db: Database connection
	:type db: AsyncDatabase
	:return: Updated user data
	:rtype: dict
	:raises AppError: If passwords don't match
	"""
	existing = None

	if user.id is not None:
		existing = user_repo.get_user_by_id(user.id, db)
	elif user.email is not None:
		existing = user_repo.get_user_by_email(user.email, db)
	else:
		raise AppError(status_code=400, message="User identification missing!")

	if not existing:
		raise AppError(status_code=400, message="User not found!")

	if user.new_password != user.confirmation_password:
		raise AppError(status_code=400, message="Passwords do not match")

	if not verify_password(user.old_password, existing["password"]):
		raise AppError(status_code=400, message="Old password is incorrect")

	updated_user: dict = await user_repo.update_user_password(
		existing["_id"], get_password_hash(user.new_password), db
	)

	return updated_user
