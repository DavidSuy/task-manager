import pytest
from services.tasks import (
    process_order,
    get_task,
    get_tasks_for_user,
    create_task,
    update_task_priority,
    list_tasks,
)
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

def test_update_task_priority_valid():
    task = create_task("Task to update", 1)
    result = update_task_priority(task["id"], 5)
    assert result["priority"] == 5

def test_update_task_priority_unknown_task():
    with pytest.raises(NotFoundError):
        update_task_priority(999, 3)

def test_update_task_priority_too_low():
    task = create_task("Task to update", 1)
    with pytest.raises(ValidationError):
        update_task_priority(task["id"], 0)

def test_update_task_priority_too_high():
    task = create_task("Task to update", 1)
    with pytest.raises(ValidationError):
        update_task_priority(task["id"], 6)

def test_update_task_priority_wrong_type():
    task = create_task("Task to update", 1)
    with pytest.raises(ValidationError):
        update_task_priority(task["id"], "high")

def test_update_task_priority_bool():
    task = create_task("Task to update", 1)
    with pytest.raises(ValidationError):
        update_task_priority(task["id"], True)

def test_list_tasks_no_filter_includes_created_tasks():
    task_a = create_task("List task A", 1)
    task_b = create_task("List task B", 1)
    result_ids = {task["id"] for task in list_tasks()}
    assert {task_a["id"], task_b["id"]} <= result_ids

def test_list_tasks_filtered_by_priority():
    task = create_task("Priority five task", 1, priority=5)
    result = list_tasks(priority=5)
    assert task["id"] in {t["id"] for t in result}
    assert all(t["priority"] == 5 for t in result)

def test_list_tasks_filter_excludes_other_priorities():
    task = create_task("Priority two task", 1, priority=2)
    result = list_tasks(priority=5)
    assert task["id"] not in {t["id"] for t in result}

def test_list_tasks_invalid_priority_too_low():
    with pytest.raises(ValidationError):
        list_tasks(priority=0)

def test_list_tasks_invalid_priority_too_high():
    with pytest.raises(ValidationError):
        list_tasks(priority=6)

def test_list_tasks_invalid_priority_wrong_type():
    with pytest.raises(ValidationError):
        list_tasks(priority="high")

def test_list_tasks_invalid_priority_bool():
    with pytest.raises(ValidationError):
        list_tasks(priority=True)
