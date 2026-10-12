import pytest
from services.tasks import process_order, get_task, get_tasks_for_user, create_task
from utils.errors import NotFoundError, ValidationError

def test_process_order_valid():
    result = process_order(1)
    assert result["done"] is True

def test_process_order_invalid():
    with pytest.raises(Exception):
        process_order(999)

def test_get_task_valid():
    result = get_task(2)
    assert result["title"] == "Write report"

def test_get_task_invalid():
    with pytest.raises(Exception):
        get_task(999)

def test_get_tasks_for_user_valid():
    result = get_tasks_for_user(1)
    assert {task["id"] for task in result} == {1, 2}

def test_get_tasks_for_user_invalid():
    with pytest.raises(NotFoundError):
        get_tasks_for_user(999)

def test_create_task_default_priority():
    result = create_task("New task", 1)
    assert result["priority"] == 3

def test_create_task_explicit_priority():
    result = create_task("New task", 1, priority=5)
    assert result["priority"] == 5

def test_create_task_invalid_priority_too_low():
    with pytest.raises(ValidationError):
        create_task("New task", 1, priority=0)

def test_create_task_invalid_priority_too_high():
    with pytest.raises(ValidationError):
        create_task("New task", 1, priority=6)

def test_create_task_invalid_priority_wrong_type():
    with pytest.raises(ValidationError):
        create_task("New task", 1, priority="high")

def test_create_task_invalid_priority_bool():
    with pytest.raises(ValidationError):
        create_task("New task", 1, priority=True)

def test_create_task_unknown_user():
    with pytest.raises(NotFoundError):
        create_task("New task", 999)
