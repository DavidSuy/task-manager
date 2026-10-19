from schemas.tags import Tag
from utils.errors import ValidationError

TAGS: dict[int, Tag] = {}

def create_tag(name: str) -> Tag:
    """Create a new tag.

    Args:
        name: The tag's display name.

    Returns:
        The newly created tag record.

    Raises:
        ValidationError: If name is empty.
    """
    if not name or not name.strip():
        raise ValidationError("name", "cannot be empty")
    new_id = max(TAGS.keys(), default=0) + 1
    TAGS[new_id] = {"id": new_id, "name": name}
    return TAGS[new_id]
