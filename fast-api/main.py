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
# BASE_PROJECT_PATH = "projects"
BASE_PROJECT_PATH = Path(os.path.dirname(os.path.abspath(__file__))) / "projects"
INPUT_PATH = BASE_PROJECT_PATH.absolute()
# INPUT_PATH = Path(BASE_PROJECT_PATH).absolute()
MEMORY_PATH = INPUT_PATH / "memory"
WORKSPACE_PATH = INPUT_PATH / "workspace"
ARCHIVE_PATH = INPUT_PATH / "archive"
STEPS_CONFIG = StepsConfig.DEFAULT


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
def hello_world():
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
    asyncio.create_task(run_engineer(app_name, json_data["message"]))

    return JSONResponse(
        content={"result": "Your request has been acknowledged and is being processed."}
    )


async def run_engineer(app_name, message):
    ai, dbs = initialize(app_name)

    dbs.input["prompt"] = message

    steps_config = StepsConfig.SIMPLE
    steps = STEPS[steps_config]
    for step in steps:
        messages = step(ai, dbs)
        dbs.logs[step.__name__] = AI.serialize_messages(messages)


@app.get("/progress")
def report_progress():
    # This function will report the progress of the request
    # For simplicity, let's assume we have a global variable that holds the progress
    global progress
    return {"progress": progress}
