"""Module for password hashing and verification operations using Argon2."""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()


def verify_need_rehash(hashed_password: str) -> bool:
    """Check if a hashed password needs to be rehashed.

    :param hashed_password: Hashed password
    :type hashed_password: str
    :return: True if the password needs rehashing, False otherwise
    :rtype: bool
    """
    return ph.check_needs_rehash(hashed_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify if a plain password matches the hash.

    :param plain_password: Plain text password
    :type plain_password: str
    :param hashed_password: Hashed password
    :type hashed_password: str
    :return: True if password matches the hash, False otherwise
    :rtype: bool
    """
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False


def get_password_hash(password: str) -> str:
    """Generate a password hash using Argon2.

    :param password: Plain text password
    :type password: str
    :return: Password hash
    :rtype: str
    """
    return ph.hash(password)
