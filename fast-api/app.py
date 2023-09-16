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

from gpt_engineer.ai import AI
from gpt_engineer.db import DB, DBs
from gpt_engineer.steps import STEPS, Config as StepsConfig
from constants import *
from routes import *

app = FastAPI()

# Global dictionary to hold the status of each operation
operation_status = {}
operation_progress = {}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Load environment variables
def load_env_if_needed():
    if os.getenv("OPENAI_API_KEY") is None:
        load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")


# Initialize AI and DBs
def initialize(app_name):
    project_path = Path(BASE_PROJECT_PATH) / app_name
    memory_path = project_path / "memory"
    workspace_path = project_path / "workspace"
    archive_path = project_path / "archive"

    ai = AI(
        model_name=MODEL,
        temperature=TEMPERATURE,
        azure_endpoint=AZURE_ENDPOINT,
    )

    dbs = DBs(
        memory=DB(memory_path),
        logs=DB(memory_path / "logs"),
        input=DB(project_path),
        workspace=DB(workspace_path),
        preprompts=DB(
            Path(__file__).parent.parent / "gpt_engineer" / "preprompts"
        ),  # Loads preprompts from the preprompts directory
        archive=DB(archive_path),
    )

    return ai, dbs

app.include_router(router)
