import pytest
from auth import (
    get_password_hash,
    verify_password,
    authenticate_user,
    create_access_token,
    get_current_user,
    register_user,
)


def test_get_password_hash():
    password = "password"
    hashed_password = get_password_hash(password)
    assert hashed_password != password


def test_verify_password():
    password = "password"
    hashed_password = get_password_hash(password)
    assert verify_password(password, hashed_password)


def test_authenticate_user():
    username = "test"
    password = "password"
    register_user(username, password)
    assert authenticate_user(username, password) == username


def test_create_access_token():
    data = {"sub": "test"}
    token = create_access_token(data=data)
    assert isinstance(token, str)


def test_get_current_user():
    username = "test"
    password = "password"
    register_user(username, password)
    token = create_access_token(data={"sub": username})
    assert get_current_user(token) == username


def test_register_user():
    username = "test2"
    password = "password"
    assert register_user(username, password)
