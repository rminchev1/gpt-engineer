import pytest
from engineer import run_engineer


def test_run_engineer():
    app_name = "test_app"
    message = "test_message"
    current_user = "test"
    run_engineer(app_name, message, current_user)
    assert operation_status[app_name] == "Completed"
