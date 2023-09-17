import pytest
from initializer import initialize


def test_initialize():
    app_name = "test_app"
    current_user = "test"
    ai, dbs = initialize(app_name, current_user)
    assert ai is not None
    assert dbs is not None
