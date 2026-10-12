import pytest

from app import app


@pytest.fixture
def client():
    return app.test_client()


def test_create_task_no_priority_defaults_to_three(client):
    response = client.post("/api/tasks", json={"title": "New task", "user_id": 2})
    assert response.status_code == 201
    assert response.get_json()["priority"] == 3


def test_create_task_explicit_priority(client):
    response = client.post(
        "/api/tasks", json={"title": "New task", "user_id": 2, "priority": 5}
    )
    assert response.status_code == 201
    assert response.get_json()["priority"] == 5


def test_create_task_priority_too_high(client):
    response = client.post(
        "/api/tasks", json={"title": "New task", "user_id": 2, "priority": 9}
    )
    assert response.status_code == 422


def test_create_task_priority_bool_rejected(client):
    response = client.post(
        "/api/tasks", json={"title": "New task", "user_id": 2, "priority": True}
    )
    assert response.status_code == 422


def test_create_task_unknown_user(client):
    response = client.post(
        "/api/tasks", json={"title": "New task", "user_id": 999}
    )
    assert response.status_code == 404


def test_create_task_missing_title(client):
    response = client.post("/api/tasks", json={"user_id": 2})
    assert response.status_code == 422


def test_update_task_priority_success(client):
    create_response = client.post(
        "/api/tasks", json={"title": "Task to update", "user_id": 2}
    )
    task_id = create_response.get_json()["id"]
    response = client.patch(f"/api/tasks/{task_id}", json={"priority": 5})
    assert response.status_code == 200
    assert response.get_json()["priority"] == 5


def test_update_task_priority_unknown_task(client):
    response = client.patch("/api/tasks/999", json={"priority": 3})
    assert response.status_code == 404


def test_update_task_priority_invalid_too_low(client):
    create_response = client.post(
        "/api/tasks", json={"title": "Task to update", "user_id": 2}
    )
    task_id = create_response.get_json()["id"]
    response = client.patch(f"/api/tasks/{task_id}", json={"priority": 0})
    assert response.status_code == 422


def test_update_task_priority_missing_body(client):
    create_response = client.post(
        "/api/tasks", json={"title": "Task to update", "user_id": 2}
    )
    task_id = create_response.get_json()["id"]
    response = client.patch(f"/api/tasks/{task_id}", json={})
    assert response.status_code == 422
