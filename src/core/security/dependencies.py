"""Security dependencies module for authentication and authorization."""

from bson import ObjectId
from fastapi import Depends, HTTPException, status

from src.utils.db import get_conn

from .jwt import decode_jwt
from .oauth2 import oauth2_scheme


async def protect(
	token: str = Depends(oauth2_scheme),
	db=Depends(get_conn),
):
	"""Get the current user from the JWT token.

	:param token: JWT token extracted from authorization header
	:type token: str
	:param db: Database connection
	:type db: AsyncDatabase
	:return: Authenticated user data
	:rtype: dict
	:raises HTTPException: If user not found or invalid token
	"""
	token_data = decode_jwt(token)

	user = await db.users.find_one({"_id": ObjectId(token_data.id)})

	if not user:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Unauthorized access",
		)

	return user


def require_role(role: str):
	"""Create a dependency that checks if the user has the specific role.

	:param role: Role required to access the resource
	:type role: str
	:return: Role verification function
	:rtype: Callable
	"""

	async def checker(
		user=Depends(protect),
	):
		"""Check if the user has the required role.

		:param user: Authenticated user
		:return: User if they have the required role
		:raises HTTPException: If the user doesn't have the required role
		"""
		if user.role != role:
			raise HTTPException(
				status_code=status.HTTP_403_FORBIDDEN,
				detail="Forbidden access",
			)
		return user

	return checker
