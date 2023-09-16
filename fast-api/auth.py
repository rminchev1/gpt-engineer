import json
import os

from datetime import datetime, timedelta
from pathlib import Path

import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

# Constants
BASE_PROJECT_PATH = Path(os.path.dirname(os.path.abspath(__file__))) / "projects"
TOKEN_PATH = BASE_PROJECT_PATH / "tokens.json"
SECRET_KEY = "YOUR_SECRET_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str):
    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, "r") as file:
            users = json.load(file)
            if username in users and verify_password(password, users[username]):
                return username
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

def create_access_token(*, data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        with open(TOKEN_PATH, "r") as file:
            users = json.load(file)
            if username in users:
                password = users[username]
    except jwt.PyJWTError:
        raise credentials_exception
    user = authenticate_user(username, password)
    if user is None:
        raise credentials_exception
    return user

def register_user(username: str, password: str):
    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, "r") as file:
            users = json.load(file)
            if username in users:
                return False
            else:
                users[username] = get_password_hash(password)
                with open(TOKEN_PATH, "w") as file:
                    json.dump(users, file)
                return True
    else:
        with open(TOKEN_PATH, "w") as file:
            users = {username: get_password_hash(password)}
            json.dump(users, file)
        return True
