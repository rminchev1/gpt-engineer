import asyncio
import os
import shutil
import zipfile

from pathlib import Path

import openai

from auth import authenticate_user, create_access_token, get_current_user, register_user
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse
from routes import router

from gpt_engineer.ai import AI
from gpt_engineer.db import DB, DBs
from gpt_engineer.steps import STEPS, Config as StepsConfig
from constants import *
from initializer import initialize

app = FastAPI()

# Global dictionary to hold the status of each operation
operation_status = {}
operation_progress = {}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Load environment variables
def load_env_if_needed():
    """
    Function to load environment variables if they are not already loaded.
    """
    if os.getenv("OPENAI_API_KEY") is None:
        load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")


app.include_router(router)

# Now you can access the routes through the FastAPI application instance
for r in app.routes:
    print(r)

