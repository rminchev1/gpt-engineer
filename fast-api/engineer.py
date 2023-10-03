import os
from pathlib import Path
from initializer import initialize

from gpt_engineer.steps import (
    STEPS,
    improve_existing_code,
    set_improve_filelist,
)

operation_progress = {}
operation_status = {}


def run_engineer(app_name, message, current_user, steps_config):
    """
    Function to run the engineer.
    This function initializes the AI and databases, sets the input prompt, and then runs the steps defined in the steps_config.
    The progress of the operation is updated in the global dictionary operation_progress.
    Once all steps are completed, the status of the operation is updated in the global dictionary operation_status.

    Parameters:
    app_name (str): The name of the app.
    message (str): The input prompt.
    current_user (str): The current user.
    steps_config (StepsConfig): The configuration of the steps to be run.
    """
    ai, dbs = initialize(app_name, current_user)

    dbs.input["prompt"] = message

    steps = STEPS[steps_config]
    total_steps = len(steps)
    for i, step in enumerate(steps):
        messages = step(ai, dbs)
        dbs.logs[step.__name__] = ai.serialize_messages(messages)

        # Update the progress of the operation in the global dictionary
        operation_progress[current_user + app_name] = (i + 1) / total_steps * 100

        # Update the status of the operation in the global dictionary
        if (i + 1) == total_steps:
            operation_status[current_user + app_name] = "Completed"
        else:
            operation_status[current_user + app_name] = "In progress"


def run_engineer_improve(app_name, message, current_user, steps_config):
    """
    Function to run the engineer.
    This function initializes the AI and databases, sets the input prompt, and then runs the steps defined in the steps_config.
    The progress of the operation is updated in the global dictionary operation_progress.
    Once all steps are completed, the status of the operation is updated in the global dictionary operation_status.

    Parameters:
    app_name (str): The name of the app.
    message (str): The input prompt.
    current_user (str): The current user.
    steps_config (StepsConfig): The configuration of the steps to be run.
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

    improve_existing_code(ai, dbs)

    operation_status[current_user + app_name] = "Completed"


def set_improved_file_list(dbs):
    """
    Function to list all files in a given directory and write them down with their absolute paths to a file called file_list.txt.
    This function is used to keep track of all the files in the workspace.

    Parameters:
    dbs (DBs): The databases.
    """
    with open(dbs.project_metadata.path / "file_list.txt", "w") as file_obj:
        for root, dirs, files in os.walk(dbs.workspace.path):
            for file in files:
                file_path = os.path.join(dbs.workspace.path, file)
                file_obj.write(f"{file_path}\n")

