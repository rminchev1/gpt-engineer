import asyncio
from engineer import run_engineer
from fastapi import APIRouter, Depends
from gpt_engineer.steps import STEPS, Config as StepsConfig
from constants import *
from starlette.requests import Request
from app import *
from auth import *

router = APIRouter()

operation_status = {}
operation_progress = {}


@router.get("/")
async def hello_world():
    return {"message": "Hello, World!"}


@router.post("/generate")
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
    if (INPUT_PATH / current_user / app_name).exists():
        raise HTTPException(
            status_code=400,
            detail="A project with the same name already exists.",
        )

    # Create a task that will run in the background
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, run_engineer, app_name, json_data["message"], current_user)
    # Update the status of the operation in the global dictionary
    operation_status[current_user + app_name] = "In progress"
    operation_progress[current_user + app_name] = 0

    return JSONResponse(
        content={"result": "Your request has been acknowledged and is being processed."}
    )


@router.get("/progress/{app_name}")
async def report_progress(app_name: str, current_user: str = Depends(get_current_user)):
    # This function will report the progress of the request
    # It checks the global dictionary for the status of the operation
    return {
        "progress": operation_status.get(current_user + app_name, "Not started"),
        "percentage": operation_progress.get(current_user + app_name, 0),
    }


@router.get("/apps")
async def list_apps(current_user: str = Depends(get_current_user)):
    # This function will list all the apps that have been created
    # It does this by listing all the directories in the projects directory
    user_path = BASE_PROJECT_PATH / current_user
    if user_path.exists():
        return {"apps": [d.name for d in user_path.iterdir() if d.is_dir()]}
    else:
        return {"apps": []}


@router.delete("/delete/{app_name}")
async def delete_app(app_name: str, current_user: str = Depends(get_current_user)):
    # This function will delete the app with the given name
    # It does this by deleting the directory associated with the app name
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
    # This function will allow the user to download the app with the given name
    # It does this by creating a zip file of the app's directory and returning it as a response
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


@router.post("/token")
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


@router.post("/register")
async def register(request: Request):
    json_data = await request.json()
    username = json_data["username"]
    password = json_data["password"]

    user = register_user(username, password)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists",
        )

    return {"message": "User registered successfully"}
