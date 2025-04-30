from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Security settings
# SECRET_KEY: Used for signing JWT tokens - should be kept secret in production
# ALGORITHM: Specifies the algorithm used for JWT token signing
# ACCESS_TOKEN_EXPIRE_MINUTES: Controls how long tokens remain valid
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"  # Change in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
# pwd_context: Handles password hashing and verification using bcrypt
# oauth2_scheme: FastAPI dependency that extracts the JWT token from the Authorization header
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Models
# Token: Response model for successful authentication
class Token(BaseModel):
    access_token: str
    token_type: str

# TokenData: Internal model for decoded token data
class TokenData(BaseModel):
    username: Optional[str] = None

# User: Base user model for API responses (excludes password)
class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = False

# UserInDB: Extended user model that includes the hashed password (for internal use)
class UserInDB(User):
    hashed_password: str

# UserCreate: Model for user registration requests
class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: str

# Mock user database - replace with actual DB in production
# Contains pre-defined admin user with hashed password
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "HR Admin",
        "email": "admin@example.com",
        "hashed_password": pwd_context.hash("adminpassword"),
        "disabled": False,
    }
}

# Helper functions
# Verifies if a plain password matches a hashed password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Generates a password hash using bcrypt
def get_password_hash(password):
    return pwd_context.hash(password)

# Retrieves a user from the database by username
def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None

# Authenticates a user by verifying username and password
def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# Creates a JWT access token with optional expiration time
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# FastAPI dependency that extracts and validates the JWT token
# Returns the current authenticated user or raises an exception
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        # Handle invalid tokens
        raise credentials_exception
    # Get the user from the database
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

# FastAPI dependency that checks if the authenticated user is active
# Used to prevent disabled users from accessing protected resources
async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user





