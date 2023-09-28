from fastapi import APIRouter, Depends, HTTPException
from auth import authenticate_user, create_access_token, register_user
from pydantic import BaseModel

router = APIRouter()


class LoginPayload(BaseModel):
    username: str
    password: str


@router.post("/token")
async def login(payload: LoginPayload):
    """
    Function to login a user.
    """
    username = payload.username
    password = payload.password

    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(data={"sub": username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register")
async def register(payload: LoginPayload):
    """
    Function to register a user.
    """
    username = payload.username
    password = payload.password

    user = register_user(username, password)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists",
        )

    return {"message": "User registered successfully"}
