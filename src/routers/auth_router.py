"""Authentication routes module."""

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pymongo.asynchronous.database import AsyncDatabase

from src.core.security.oauth2 import oauth2_scheme
from src.models.auth import Token
from src.models.user import UserCreate, UserOut
from src.services import auth_service
from src.utils.db import get_conn

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(
	form_data: OAuth2PasswordRequestForm = Depends(),
	db: AsyncDatabase = Depends(get_conn),
):
	"""Login endpoint that returns an access token.

	:param form_data: Form data with email and password
	:type form_data: OAuth2PasswordRequestForm
	:param db: Database connection
	:type db: AsyncDatabase
	:return: Access token and token type
	:rtype: Token
	"""
	access_token = await auth_service.authenticate_user(
		email=form_data.username,
		password=form_data.password,
		db=db,
	)

	return {
		"access_token": access_token,
		"token_type": "bearer",
	}


@router.post("/signup", response_model=UserOut)
async def signup(
	user: UserCreate,
	db: AsyncDatabase = Depends(get_conn),
):
	"""User registration endpoint.

	:param user: User data to be created
	:type user: UserCreate
	:param db: Database connection
	:type db: AsyncDatabase
	:return: Created user data
	:rtype: UserOut
	"""
	user_out = await auth_service.signup_user(user, db)
	return user_out


@router.get("/me", response_model=UserOut)
async def read_users_me(
	token: str = Depends(oauth2_scheme),
	db: AsyncDatabase = Depends(get_conn),
):
	"""Endpoint that returns authenticated user data.

	:param token: JWT authentication token
	:type token: str
	:param db: Database connection
	:type db: AsyncDatabase
	:return: Authenticated user data
	:rtype: UserOut
	"""
	return await auth_service.get_current_user(token, db)
