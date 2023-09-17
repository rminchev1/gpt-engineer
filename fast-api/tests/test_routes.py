import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_hello_world():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}


def test_generate():
    response = client.post(
        "/generate", json={"appName": "test_app", "message": "test_message"}
    )
    assert response.status_code == 200


def test_progress():
    response = client.get("/progress/test_app")
    assert response.status_code == 200


def test_list_apps():
    response = client.get("/apps")
    assert response.status_code == 200


def test_delete_app():
    response = client.delete("/delete/test_app")
    assert response.status_code == 200


def test_download_app():
    response = client.get("/download/test_app")
    assert response.status_code == 200


def test_login():
    response = client.post("/token", json={"username": "test", "password": "password"})
    assert response.status_code == 200


def test_register():
    response = client.post(
        "/register", json={"username": "test2", "password": "password"}
    )
    assert response.status_code == 200
