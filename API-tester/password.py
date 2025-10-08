from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
def hash_pwd(password: str) -> str:
    """Hash the password"""

    return pwd_context.hash(password)