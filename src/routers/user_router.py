from fastapi import APIRouter, Depends
from pymongo.asynchronous.database import AsyncDatabase

from src.core.security.dependencies import require_role
from src.models.user import User, UserOut, UserUpdatePass
from src.repos import user_repo
from src.services import user_service
from src.utils.db import get_conn

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserOut])
async def read_users(
	user: User = Depends(require_role("admin")),
	db: AsyncDatabase = Depends(get_conn),
):
	"""Endpoint to retrieve all users. Accessible only by admin users.

	:param user: Current authenticated user
	:type user: User
	:param db: Database connection
	:type db: AsyncDatabase
	:return: List of all users
	:rtype: list[UserOut]
	"""
	users = await user_repo.get_all_users(db)
	return users


@router.get("/{user_id}", response_model=UserOut)
async def read_user_by_id(
	user_id: str,
	user: User = Depends(require_role("admin")),
	db: AsyncDatabase = Depends(get_conn),
):
	"""Endpoint to retrieve a user by their ID.

	:param user_id: The ID of the user to retrieve
	:type user_id: str
	:param user: Current authenticated user
	:type user: User
	:param db: Database connection
	:type db: AsyncDatabase
	:return: The user data if found
	:rtype: UserOut
	"""
	user_data = await user_service.get_user_by_id(user_id, db)
	return user_data


@router.patch("update-password", response_model=UserOut)
async def update_user_password(
	user_update: UserUpdatePass,
	db: AsyncDatabase = Depends(get_conn),
):
	"""Endpoint to update the password of the current authenticated user.

	:param user_update: Data for updating the user's password
	:type user_update: UserUpdatePass
	:param user: Current authenticated user
	:type user: User
	:param db: Database connection
	:type db: AsyncDatabase
	:return: Updated user data
	:rtype: UserOut
	"""
	updated_user = await user_service.update_user_pass(user_update, db)
	return updated_user
