import asyncio
import os

from pathlib import Path

import openai

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from gpt_engineer.ai import AI
from gpt_engineer.db import DB, DBs
from gpt_engineer.steps import STEPS, Config as StepsConfig

app = FastAPI()

# Constants
MODEL = "gpt-4"
TEMPERATURE = 1.0
AZURE_ENDPOINT = ""
BASE_PROJECT_PATH = Path(os.path.dirname(os.path.abspath(__file__))) / "projects"
INPUT_PATH = BASE_PROJECT_PATH.absolute()
MEMORY_PATH = INPUT_PATH / "memory"
WORKSPACE_PATH = INPUT_PATH / "workspace"
ARCHIVE_PATH = INPUT_PATH / "archive"
STEPS_CONFIG = StepsConfig.DEFAULT

# Global dictionary to hold the status of each operation
operation_status = {}


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


@app.get("/")
async def hello_world():
    return {"message": "Hello, World!"}


@app.post("/generate")
async def use_engineer(request: Request):
    json_data = await request.json()
    app_name = json_data["appName"]

    # Check if appName is not empty and doesn't contain any white spaces
    if not app_name or " " in app_name:
        raise HTTPException(
            status_code=400,
            detail="Invalid appName."
            + "It should not be empty and should not contain any white spaces.",
        )

    # Check if a directory with the same name already exists
    if (INPUT_PATH / app_name).exists():
        raise HTTPException(
            status_code=400,
            detail="A project with the same name already exists.",
        )

    # Create a task that will run in the background
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, run_engineer, app_name, json_data["message"])

    # Update the status of the operation in the global dictionary
    operation_status[app_name] = "In progress"

    return JSONResponse(
        content={"result": "Your request has been acknowledged and is being processed."}
    )


def run_engineer(app_name, message):
    ai, dbs = initialize(app_name)

    dbs.input["prompt"] = message

    steps_config = StepsConfig.SIMPLE
    steps = STEPS[steps_config]
    for step in steps:
        messages = step(ai, dbs)
        dbs.logs[step.__name__] = AI.serialize_messages(messages)

    # Update the status of the operation in the global dictionary
    operation_status[app_name] = "Completed"


@app.get("/progress/{app_name}")
async def report_progress(app_name: str):
    # This function will report the progress of the request
    # It checks the global dictionary for the status of the operation
    return {"progress": operation_status.get(app_name, "Not started")}
