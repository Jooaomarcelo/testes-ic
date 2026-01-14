"""Authentication models module."""

from .base_model import CustomBaseModel


class Token(CustomBaseModel):
    """Authentication token response model."""

    access_token: str
    token_type: str


class TokenData(CustomBaseModel):
    """Data contained in JWT token model."""

    id: str | None = None
    exp: int | None = None
    iat: int | None = None
