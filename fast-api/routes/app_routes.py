import sys

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth import get_current_user
import engineer
from constants import *

import asyncio
import shutil
import zipfile
import os
import json
import uuid
from starlette.responses import FileResponse, JSONResponse

from gpt_engineer.steps import (
    STEPS,
    Config as StepsConfig,
    set_improve_filelist,
    get_improve_prompt,
    improve_existing_code,
)

router = APIRouter()

operation_status = {}
operation_progress = {}

class GeneratePayload(BaseModel):
    appName: str
    message: str


@router.post("/generate")
async def use_engineer(
    payload: GeneratePayload, current_user: str = Depends(get_current_user)
):
    """
    Endpoint to generate a new project using the engineer tool.
    The request body should contain a JSON object with the following properties:
    - appName: The name of the application to be generated.
    - message: The message to be used as a prompt for the engineer tool.
    """
    app_name = payload.appName

    if not app_name or " " in app_name:
        raise HTTPException(
            status_code=400,
            detail="Invalid appName."
            + "It should not be empty and should not contain any white spaces.",
        )

    if (INPUT_PATH / current_user / app_name).exists():
        raise HTTPException(
            status_code=400,
            detail="A project with the same name already exists.",
        )

    loop = asyncio.get_event_loop()
    loop.run_in_executor(
        None, engineer.run_engineer, app_name, payload.message, current_user, StepsConfig.SIMPLE
    )    
    engineer.operation_status[current_user + app_name] = "In progress"
    engineer.operation_progress[current_user + app_name] = 0

    project_path = BASE_PROJECT_PATH / current_user / app_name
    prompts_path = project_path / "prompts.json"
    os.makedirs(project_path, exist_ok=True)
    if prompts_path.exists():
        with open(prompts_path, "r") as file:
            prompts = json.load(file)
    else:
        prompts = {}

    prompt_id = str(uuid.uuid4())
    prompts[prompt_id] = payload.message

    with open(prompts_path, "w") as file:
        json.dump(prompts, file)

    return JSONResponse(
        content={"result": "Your request has been acknowledged and is being processed."}
    )


@router.get("/progress/{app_name}")
async def report_progress(app_name: str, current_user: str = Depends(get_current_user)):
    """
    Endpoint to get the progress of a project generation operation.
    The path parameter should be the name of the application.
    """
    return {
        "progress": engineer.operation_status.get(current_user + app_name, "Not started"),
        "percentage": engineer.operation_progress.get(current_user + app_name, 0),
    }


@router.get("/apps")
async def list_apps(current_user: str = Depends(get_current_user)):
    """
    Endpoint to get a list of all applications created by the current user.
    """
    user_path = BASE_PROJECT_PATH / current_user
    if user_path.exists():
        return {"apps": [d.name for d in user_path.iterdir() if d.is_dir()]}
    else:
        return {"apps": []}


@router.delete("/delete/{app_name}")
async def delete_app(app_name: str, current_user: str = Depends(get_current_user)):
    """
    Endpoint to delete an application.
    The path parameter should be the name of the application to be deleted.
    """
    app_path = BASE_PROJECT_PATH / current_user / app_name
    if app_path.exists() and app_path.is_dir():
        shutil.rmtree(app_path)
        return {"message": f"App {app_name} has been successfully deleted."}
    else:
        raise HTTPException(
            status_code=404,
            detail=f"App {app_name} does not exist.",
        )


@router.get("/download/{app_name}")
async def download_app(app_name: str, current_user: str = Depends(get_current_user)):
    """
    Endpoint to download an application as a zip file.
    The path parameter should be the name of the application to be downloaded.
    """
    app_path = BASE_PROJECT_PATH / current_user / app_name
    if app_path.exists() and app_path.is_dir():
        zip_file_path = BASE_PROJECT_PATH / current_user / f"{app_name}.zip"
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


@router.post("/run_prompt/{app_name}/{prompt_id}")
async def run_prompt(
    app_name: str, prompt_id: str, current_user: str = Depends(get_current_user)
):
    """
    Endpoint to run a prompt on an existing application.
    The path parameters should be the name of the application and the id of the prompt.
    """
    project_path = BASE_PROJECT_PATH / current_user / app_name
    if not project_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Project {app_name} does not exist.",
        )

    prompts_path = project_path / "prompts.json"
    if prompts_path.exists():
        with open(prompts_path, "r") as file:
            prompts = json.load(file)
    else:
        prompts = {}

    if prompt_id not in prompts:
        raise HTTPException(
            status_code=404,
            detail=f"Prompt does not exist.",
        )

    loop = asyncio.get_event_loop()
    loop.run_in_executor(
        None,
        engineer.run_engineer_improve,
        app_name,
        prompts[prompt_id],
        current_user,
        StepsConfig.IMPROVE_CODE,
    )
    engineer.operation_status[current_user + app_name + prompt_id] = "In progress"
    engineer.operation_progress[current_user + app_name + prompt_id] = 0

    return JSONResponse(
        content={"result": "Your request has been acknowledged and is being processed."}
    )


@router.get("/files/{app_name}")
async def list_files(app_name: str, current_user: str = Depends(get_current_user)):
    """
    Endpoint to get a list of all files in an application.
    The path parameter should be the name of the application.
    """
    app_path = BASE_PROJECT_PATH / current_user / app_name / "workspace"
    if app_path.exists() and app_path.is_dir():
        return {
            "files": [
                str(f.relative_to(app_path)) for f in app_path.glob("**/*") if f.is_file()
            ]
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=f"App {app_name} does not exist.",
        )


@router.get("/file/{app_name}/{file_path:path}")
async def get_file_content(
    app_name: str, file_path: str, current_user: str = Depends(get_current_user)
):
    """
    Endpoint to get the content of a file in an application.
    The path parameters should be the name of the application and the path of the file.
    """
    app_path = BASE_PROJECT_PATH / current_user / app_name / "workspace" / file_path
    if app_path.exists() and app_path.is_file():
        with open(app_path, "r") as file:
            content = file.read()
        return {"content": content}
    else:
        raise HTTPException(
            status_code=404,
            detail=f"File {file_path} does not exist in App {app_name}.",
        )