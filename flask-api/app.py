import os

from pathlib import Path

import openai

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from gpt_engineer.ai import AI
from gpt_engineer.db import DB, DBs
from gpt_engineer.steps import STEPS, Config as StepsConfig

app = Flask(__name__)

# Constants
MODEL = "gpt-4"
TEMPERATURE = 1.0
AZURE_ENDPOINT = ""
BASE_PROJECT_PATH = "flask-api/projects"
INPUT_PATH = Path(BASE_PROJECT_PATH).absolute()
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


@app.route("/app", methods=["GET"])
def hello_world():
    return "Hello, World!"


@app.route("/generate", methods=["POST"])
def use_engineer():
    json_data = request.get_json()
    app_name = json_data["appName"]

    # Check if appName is not empty and doesn't contain any white spaces
    if not app_name or " " in app_name:
        return (
            jsonify(
                {
                    "error": "Invalid appName."
                    + "It should not be empty and should not contain any white spaces."
                }
            ),
            400,
        )

    # Check if a directory with the same name already exists
    if (INPUT_PATH / app_name).exists():
        return (
            jsonify(
                {
                    "error": "A project with the same name already exists."
                    + "Please choose a different name."
                }
            ),
            400,
        )

    ai, dbs = initialize(app_name)

    dbs.input["prompt"] = json_data["message"]

    steps_config = StepsConfig.SIMPLE
    steps = STEPS[steps_config]
    for step in steps:
        messages = step(ai, dbs)
        dbs.logs[step.__name__] = AI.serialize_messages(messages)

    return jsonify({"result": "hello"})


if __name__ == "__main__":
    app.run(debug=True)
