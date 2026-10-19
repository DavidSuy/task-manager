import pytest

from services.tags import create_tag
from utils.errors import ValidationError


def test_create_tag_happy_path():
    tag = create_tag("urgent")
    assert tag["name"] == "urgent"
    assert isinstance(tag["id"], int)


def test_create_tag_empty_name():
    with pytest.raises(ValidationError):
        create_tag("")


def test_create_tag_whitespace_name():
    with pytest.raises(ValidationError):
        create_tag("   ")


def test_create_tag_none_name():
    with pytest.raises(ValidationError):
        create_tag(None)


def test_create_tag_increments_id():
    first = create_tag("first-tag")
    second = create_tag("second-tag")
    assert second["id"] == first["id"] + 1
