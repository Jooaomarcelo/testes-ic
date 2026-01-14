"""User repository for database operations."""

from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase

from src.models.user import User


async def get_users(db: AsyncDatabase):
	"""
	Retrieve all users from the database.

	:param db: The database connection.
	:type db: AsyncDatabase
	:return: A list of all user documents.
	:rtype: list[dict]
	"""
	users = db.get_collection("users").find().to_list()
	return users


async def get_user_by_email(email: str, db: AsyncDatabase):
	"""
	Retrieve a user from the database by email.

	:param email: The email of the user to retrieve.
	:type email: str
	:param db: The database connection.
	:type db: AsyncDatabase
	:return: The user document if found, otherwise None.
	:rtype: dict | None
	"""
	user = await db.get_collection("users").find_one({"email": email})
	return user


async def get_user_by_id(user_id: str, db: AsyncDatabase):
	"""
	Retrieve a user from the database by their ID.

	:param user_id: The ID of the user to retrieve.
	:type user_id: str
	:param db: The database connection.
	:type db: AsyncDatabase
	:return: The user document if found, otherwise None.
	:rtype: dict | None
	"""
	user = await db.get_collection("users").find_one({"_id": ObjectId(user_id)})
	return user


async def create_user(user: User, db: AsyncDatabase):
	"""
	Create a new user in the database.

	:param user: The user data to create.
	:type user: User
	:param db: The database connection.
	:type db: AsyncDatabase
	:return: The created user document.
	:rtype: dict
	"""
	res = await db.get_collection("users").insert_one(user.model_dump(mode="json"))
	created_user = await db.get_collection("users").find_one({"_id": res.inserted_id})
	return created_user


async def update_user_password(
	user_id: str, new_hashed_password: str, db: AsyncDatabase
):
	"""
	Update a user's password in the database.

	:param user_id: The ID of the user to update.
	:type user_id: str
	:param new_hashed_password: The new hashed password.
	:type new_hashed_password: str
	:param db: The database connection.
	:type db: AsyncDatabase
	:return: The updated user document.
	:rtype: dict | None
	"""
	await db.get_collection("users").update_one(
		{"_id": ObjectId(user_id)}, {"$set": {"password": new_hashed_password}}
	)
	updated_user = await db.get_collection("users").find_one({"_id": ObjectId(user_id)})
	return updated_user
