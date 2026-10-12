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


def test_list_tasks_route_no_filter(client):
    create_response = client.post(
        "/api/tasks", json={"title": "List me", "user_id": 2}
    )
    task_id = create_response.get_json()["id"]
    response = client.get("/api/tasks")
    assert response.status_code == 200
    assert task_id in {task["id"] for task in response.get_json()}


def test_list_tasks_route_filtered_by_priority(client):
    create_response = client.post(
        "/api/tasks", json={"title": "List me", "user_id": 2, "priority": 5}
    )
    task_id = create_response.get_json()["id"]
    response = client.get("/api/tasks?priority=5")
    assert response.status_code == 200
    tasks = response.get_json()
    assert task_id in {task["id"] for task in tasks}
    assert all(task["priority"] == 5 for task in tasks)


def test_list_tasks_route_priority_out_of_range(client):
    response = client.get("/api/tasks?priority=9")
    assert response.status_code == 422
    assert "between 1 and 5" in response.get_json()["error"]


def test_list_tasks_route_priority_non_numeric(client):
    response = client.get("/api/tasks?priority=abc")
    assert response.status_code == 422
    assert "between 1 and 5" not in response.get_json()["error"]
