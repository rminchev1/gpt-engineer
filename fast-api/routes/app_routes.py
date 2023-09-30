import sys

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth import get_current_user
from engineer import run_engineer, run_engineer_improve
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
        None, run_engineer, app_name, payload.message, current_user, StepsConfig.SIMPLE
    )
    operation_status[current_user + app_name] = "In progress"
    operation_progress[current_user + app_name] = 0

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
    return {
        "progress": operation_status.get(current_user + app_name, "Not started"),
        "percentage": operation_progress.get(current_user + app_name, 0),
    }


@router.get("/apps")
async def list_apps(current_user: str = Depends(get_current_user)):
    user_path = BASE_PROJECT_PATH / current_user
    if user_path.exists():
        return {"apps": [d.name for d in user_path.iterdir() if d.is_dir()]}
    else:
        return {"apps": []}


@router.delete("/delete/{app_name}")
async def delete_app(app_name: str, current_user: str = Depends(get_current_user)):
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
        run_engineer_improve,
        app_name,
        prompts[prompt_id],
        current_user,
        StepsConfig.IMPROVE_CODE,
    )
    operation_status[current_user + app_name + prompt_id] = "In progress"
    operation_progress[current_user + app_name + prompt_id] = 0

    return JSONResponse(
        content={"result": "Your request has been acknowledged and is being processed."}
    )

@router.get("/files/{app_name}")
async def list_files(app_name: str, current_user: str = Depends(get_current_user)):
    """
    Route to list all the files in the app.
    The current user is determined using the Depends function from FastAPI.
    The function then lists all the files in the app directory and returns them.
    """
    app_path = BASE_PROJECT_PATH / current_user / app_name / "workspace"
    if app_path.exists() and app_path.is_dir():
        return {"files": [f.name for f in app_path.glob("**/*") if f.is_file()]}
    else:
        raise HTTPException(
            status_code=404,
            detail=f"App {app_name} does not exist.",
        )


