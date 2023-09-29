import os
from pathlib import Path
from initializer import initialize

from gpt_engineer.steps import (
    STEPS,
    Config as StepsConfig,
    get_improve_prompt,
    improve_existing_code,
    set_improve_filelist,
)

operation_progress = {}
operation_status = {}


def run_engineer(app_name, message, current_user, steps_config):
    """
    Function to run the engineer.
    """
    ai, dbs = initialize(app_name, current_user)

    dbs.input["prompt"] = message

    steps = STEPS[steps_config]
    total_steps = len(steps)
    for i, step in enumerate(steps):
        messages = step(ai, dbs)
        dbs.logs[step.__name__] = ai.serialize_messages(messages)

        # Update the progress of the operation in the global dictionary
        operation_progress[app_name] = (i + 1) / total_steps * 100

    # Update the status of the operation in the global dictionary
    operation_status[app_name] = "Completed"


def run_engineer_improve(app_name, message, current_user, steps_config):
    """
    Function to run the engineer.
    """

    app_base_path = (
        Path(os.path.dirname(os.path.abspath(__file__)))
        / "projects"
        / current_user
        / app_name
    )

    ai, dbs = initialize(app_name, current_user, app_base_path)

    dbs.input["prompt"] = message

    set_improved_file_list(dbs)

    set_improve_filelist(ai, dbs)

    improve_existing_code(ai, dbs)

    operation_status[app_name] = "Completed"


def set_improved_file_list(dbs):
    """
    Function to list all files in a given directory and write them down with their absolute paths to a file called file_list.txt.
    """
    with open(dbs.project_metadata.path / "file_list.txt", "w") as file_obj:
        for root, dirs, files in os.walk(dbs.workspace.path):
            for file in files:
                file_path = os.path.join(dbs.workspace.path, file)
                file_obj.write(f"{file_path}\n")

