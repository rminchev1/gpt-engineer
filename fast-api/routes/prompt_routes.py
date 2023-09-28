from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth import get_current_user
from constants import *
import uuid
import json

router = APIRouter()


class PromptPayload(BaseModel):
    prompt: str


class PromptIdPayload(BaseModel):
    prompt_id: str


class UpdatePromptPayload(BaseModel):
    prompt_id: str
    new_prompt: str


@router.post("/add_prompt/{app_name}")
async def add_prompt(
    app_name: str, payload: PromptPayload, current_user: str = Depends(get_current_user)
):
    """
    Function to add a new prompt to the project.
    """
    prompt = payload.prompt

    # Check if the project exists
    project_path = BASE_PROJECT_PATH / current_user / app_name
    if not project_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Project {app_name} does not exist.",
        )

    # Add the prompt to the project's prompts file
    prompts_path = project_path / "prompts.json"
    if prompts_path.exists():
        with open(prompts_path, "r") as file:
            prompts = json.load(file)
    else:
        prompts = {}

    prompt_id = str(uuid.uuid4())
    prompts[prompt_id] = prompt

    with open(prompts_path, "w") as file:
        json.dump(prompts, file)

    return {"message": f"Prompt added to project {app_name}."}


@router.delete("/delete_prompt/{app_name}")
async def delete_prompt(
    app_name: str, payload: PromptIdPayload, current_user: str = Depends(get_current_user)
):
    """
    Function to delete a prompt from the project.
    """
    prompt_id = payload.prompt_id

    # Check if the project exists
    project_path = BASE_PROJECT_PATH / current_user / app_name
    if not project_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Project {app_name} does not exist.",
        )

    # Delete the prompt from the project's prompts file
    prompts_path = project_path / "prompts.json"
    with open(prompts_path, "r") as file:
        prompts = json.load(file)

    if prompt_id in prompts:
        del prompts[prompt_id]
        with open(prompts_path, "w") as file:
            json.dump(prompts, file)
        return {"message": f"Prompt deleted from project {app_name}."}
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Prompt does not exist.",
        )


@router.put("/update_prompt/{app_name}")
async def update_prompt(
    app_name: str,
    payload: UpdatePromptPayload,
    current_user: str = Depends(get_current_user),
):
    """
    Function to update a prompt in the project.
    """
    prompt_id = payload.prompt_id
    new_prompt = payload.new_prompt

    # Check if the project exists
    project_path = BASE_PROJECT_PATH / current_user / app_name
    if not project_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Project {app_name} does not exist.",
        )

    # Update the prompt in the project's prompts file
    prompts_path = project_path / "prompts.json"
    with open(prompts_path, "r") as file:
        prompts = json.load(file)

    if prompt_id in prompts:
        prompts[prompt_id] = new_prompt
        with open(prompts_path, "w") as file:
            json.dump(prompts, file)
        return {"message": f"Prompt updated in project {app_name}."}
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Prompt does not exist.",
        )


@router.get("/prompts/{app_name}")
async def list_prompts(app_name: str, current_user: str = Depends(get_current_user)):
    """
    Function to list all the prompts in the project.
    """
    # This function will list all the prompts in the project
    # It does this by reading the prompts file in the project directory

    # Check if the project exists
    project_path = BASE_PROJECT_PATH / current_user / app_name
    if not project_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Project {app_name} does not exist.",
        )

    # Read the prompts from the project's prompts file
    prompts_path = project_path / "prompts.json"
    if prompts_path.exists():
        with open(prompts_path, "r") as file:
            prompts = json.load(file)
    else:
        prompts = {}

    return {"prompts": prompts}
