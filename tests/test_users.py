import pytest

from services.users import (
    create_user,
    get_notification_pref,
    list_users,
    update_notification_pref,
)
from utils.errors import NotFoundError, ValidationError


def test_get_notification_pref_default_none():
    user = create_user("Test User", "test@example.com")
    result = get_notification_pref(user["id"])
    assert result["notification_pref"] == "none"


def test_update_notification_pref_email():
    user = create_user("Test User", "test@example.com")
    result = update_notification_pref(user["id"], "email")
    assert result["notification_pref"] == "email"


def test_update_notification_pref_sms():
    user = create_user("Test User", "test@example.com")
    result = update_notification_pref(user["id"], "sms")
    assert result["notification_pref"] == "sms"


def test_update_notification_pref_invalid_value():
    user = create_user("Test User", "test@example.com")
    with pytest.raises(ValidationError):
        update_notification_pref(user["id"], "pigeon")


def test_update_notification_pref_none_value():
    user = create_user("Test User", "test@example.com")
    with pytest.raises(ValidationError):
        update_notification_pref(user["id"], None)


def test_get_notification_pref_unknown_user():
    with pytest.raises(NotFoundError):
        get_notification_pref(999)


def test_update_notification_pref_unknown_user():
    with pytest.raises(NotFoundError):
        update_notification_pref(999, "email")


def test_list_users_includes_notification_pref():
    create_user("Test User", "test@example.com")
    for user in list_users():
        assert "notification_pref" in user
