from pathlib import Path
from gpt_engineer.ai import AI
from gpt_engineer.db import DB, DBs
from constants import *


def initialize(app_name, current_user):
    project_path = Path(BASE_PROJECT_PATH) / current_user / app_name
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
        project_metadata= project_path / ".gpteng"
    )

    return ai, dbs
