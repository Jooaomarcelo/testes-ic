"""Module for JWT operations (token creation and decoding)."""

from datetime import timedelta

from jwt import ExpiredSignatureError, InvalidTokenError, PyJWT

from src.core.config import settings
from src.models.auth import TokenData
from src.utils.app_error import AppError
from src.utils.date_now import get_utc_now


def sign_jwt(data: dict) -> str:
    """Create and sign a JWT token with the provided data.

    :param data: Data to be encoded in the token
    :type data: dict
    :return: Signed JWT token
    :rtype: str
    """
    to_encode = data.copy()
    jwt_instance = PyJWT()

    start = get_utc_now()
    expire = start + timedelta(minutes=settings.jwt_expiration_minutes)

    to_encode.update({"exp": expire, "iat": start})

    token = jwt_instance.encode(
        payload=to_encode,
        key=settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    return token


def decode_jwt(token: str) -> TokenData:
    """
    Decode a JWT token and return the payload.

    :param token: JWT token to decode
    :type token: str
    :return: Decoded token data
    :rtype: TokenData
    :raises AppError: If token has expired or is invalid
    """
    jwt_instance = PyJWT()

    try:
        payload = jwt_instance.decode(
            token,
            key=settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )

        token_data = TokenData(**payload)
        print(token_data.model_dump())
        return token_data

    except ExpiredSignatureError:
        raise AppError(status_code=401, message="Token has expired")

    except InvalidTokenError:
        raise AppError(status_code=401, message="Invalid token")
