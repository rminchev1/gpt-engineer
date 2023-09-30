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
    This function takes in a payload containing the username and password of the user.
    It then calls the authenticate_user function to check if the username and password are valid.
    If they are valid, it creates an access token for the user and returns it.
    If they are not valid, it raises an HTTPException with a status code of 400.

    Parameters:
    payload (LoginPayload): The payload containing the username and password of the user.

    Returns:
    dict: A dictionary containing the access token and the token type.
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
    This function takes in a payload containing the username and password of the user.
    It then calls the register_user function to register the user.
    If the registration is successful, it returns a success message.
    If the registration is not successful (i.e., the username already exists), it raises an HTTPException with a status code of 400.

    Parameters:
    payload (LoginPayload): The payload containing the username and password of the user.

    Returns:
    dict: A dictionary containing a success message.
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
