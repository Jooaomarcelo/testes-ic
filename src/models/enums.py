"""Application enumerations module."""

from enum import Enum


class UserRole(Enum):
    """User role types enumeration."""

    ADMIN = "admin"
    USER = "user"
