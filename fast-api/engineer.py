from initializer import initialize
from gpt_engineer.steps import STEPS, Config as StepsConfig

operation_progress = {}
operation_status = {}


def run_engineer(app_name, message, current_user):
    """
    Function to run the engineer.
    """
    ai, dbs = initialize(app_name, current_user)

    dbs.input["prompt"] = message

    steps_config = StepsConfig.SIMPLE
    steps = STEPS[steps_config]
    total_steps = len(steps)
    for i, step in enumerate(steps):
        messages = step(ai, dbs)
        dbs.logs[step.__name__] = ai.serialize_messages(messages)

        # Update the progress of the operation in the global dictionary
        operation_progress[app_name] = (i + 1) / total_steps * 100

    # Update the status of the operation in the global dictionary
    operation_status[app_name] = "Completed"
