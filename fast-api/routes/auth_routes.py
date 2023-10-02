from fastapi import APIRouter, Depends, HTTPException
from auth import authenticate_user, create_access_token, register_user, set_api_key, get_api_key, get_current_user
from pydantic import BaseModel

router = APIRouter()


class LoginPayload(BaseModel):
    username: str
    password: str


class ApiKeyPayload(BaseModel):
    api_key: str


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


@router.post("/set_api_key")
async def set_api_key_route(payload: ApiKeyPayload, current_user: str = Depends(get_current_user)):
    """
    Function to set the OpenAI API key of a user.
    This function takes in a payload containing the API key and the current user as parameters.
    It then calls the set_api_key function to set the API key of the user.
    It returns a success message.

    Parameters:
    payload (ApiKeyPayload): The payload containing the API key.
    current_user (str): The current user.

    Returns:
    dict: A dictionary containing a success message.
    """
    api_key = payload.api_key
    set_api_key(current_user, api_key)
    return {"message": "API key set successfully"}


@router.get("/get_api_key")
async def get_api_key_route(current_user: str = Depends(get_current_user)):
    """
    Function to get the OpenAI API key of a user.
    This function takes in the current user as a parameter.
    It then calls the get_api_key function to get the API key of the user.
    It returns the API key.

    Parameters:
    current_user (str): The current user.

    Returns:
    dict: A dictionary containing the API key.
    """
    api_key = get_api_key(current_user)
    return {"api_key": api_key}

