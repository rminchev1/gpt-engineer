from pathlib import Path
from gpt_engineer.ai import AI
from gpt_engineer.db import DB, DBs
from constants import *
from auth import get_api_key
import openai


def initialize(app_name, current_user, base_project_path=None):
    """
    Function to initialize the AI and databases.
    """
    openai_api_key = get_api_key(current_user)
    openai.api_key = openai_api_key    
    project_path = None

    if base_project_path is None:
        base_project_path = BASE_PROJECT_PATH
        print("Using project print.")
        project_path = Path(base_project_path) / current_user / app_name
    else:
        project_path = base_project_path

    workspace_path = project_path / "workspace"
    project_metadata_path = project_path / ".gpteng"
    memory_path = project_metadata_path / "memory"
    archive_path = project_metadata_path / "archive"

    ai = AI(
        model_name=MODEL,
        temperature=TEMPERATURE,
        azure_endpoint=AZURE_ENDPOINT,
        openai_api_key=openai_api_key
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
        project_metadata=DB(project_metadata_path),
    )

    return ai, dbs
