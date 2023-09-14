import asyncio
import os
import shutil
import zipfile

from pathlib import Path

import openai

from auth import authenticate_user, create_access_token, get_current_user
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse

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
TOKEN_PATH = BASE_PROJECT_PATH / "tokens.json"

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


@app.get("/")
async def hello_world():
    return {"message": "Hello, World!"}


@app.post("/generate")
async def use_engineer(request: Request, current_user: str = Depends(get_current_user)):
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
    operation_progress[app_name] = 0

    return JSONResponse(
        content={"result": "Your request has been acknowledged and is being processed."}
    )


def run_engineer(app_name, message):
    ai, dbs = initialize(app_name)

    dbs.input["prompt"] = message

    steps_config = StepsConfig.SIMPLE
    steps = STEPS[steps_config]
    total_steps = len(steps)
    for i, step in enumerate(steps):
        messages = step(ai, dbs)
        dbs.logs[step.__name__] = AI.serialize_messages(messages)

        # Update the progress of the operation in the global dictionary
        operation_progress[app_name] = (i + 1) / total_steps * 100

    # Update the status of the operation in the global dictionary
    operation_status[app_name] = "Completed"


@app.get("/progress/{app_name}")
async def report_progress(app_name: str, current_user: str = Depends(get_current_user)):
    # This function will report the progress of the request
    # It checks the global dictionary for the status of the operation
    return {
        "progress": operation_status.get(app_name, "Not started"),
        "percentage": operation_progress.get(app_name, 0),
    }


@app.get("/apps")
async def list_apps(current_user: str = Depends(get_current_user)):
    # This function will list all the apps that have been created
    # It does this by listing all the directories in the projects directory
    return {"apps": [d.name for d in BASE_PROJECT_PATH.iterdir() if d.is_dir()]}


@app.delete("/delete/{app_name}")
async def delete_app(app_name: str, current_user: str = Depends(get_current_user)):
    # This function will delete the app with the given name
    # It does this by deleting the directory associated with the app name
    app_path = BASE_PROJECT_PATH / app_name
    if app_path.exists() and app_path.is_dir():
        shutil.rmtree(app_path)
        return {"message": f"App {app_name} has been successfully deleted."}
    else:
        raise HTTPException(
            status_code=404,
            detail=f"App {app_name} does not exist.",
        )


@app.get("/download/{app_name}")
async def download_app(app_name: str, current_user: str = Depends(get_current_user)):
    # This function will allow the user to download the app with the given name
    # It does this by creating a zip file of the app's directory and returning it as a response
    app_path = BASE_PROJECT_PATH / app_name
    if app_path.exists() and app_path.is_dir():
        zip_file_path = BASE_PROJECT_PATH / f"{app_name}.zip"
        with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(app_path):
                for file in files:
                    zipf.write(
                        os.path.join(root, file),
                        os.path.relpath(
                            os.path.join(root, file), os.path.join(app_path, "..")
                        ),
                    )
        return FileResponse(
            path=str(zip_file_path),
            filename=f"{app_name}.zip",
            media_type="application/zip",
        )
    else:
        raise HTTPException(
            status_code=404,
            detail=f"App {app_name} does not exist.",
        )


@app.post("/token")
async def login(request: Request):
    json_data = await request.json()
    username = json_data["username"]
    password = json_data["password"]

    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(data={"sub": username})
    return {"access_token": access_token, "token_type": "bearer"}
