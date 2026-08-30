from app.semantic_memory.exceptions import SemanticMemoryValidationError


def normalized_text(value, field_name="content"):
    if not isinstance(value, str) or not value.strip():
        raise SemanticMemoryValidationError(f"{field_name} must be a non-empty string")
    return " ".join(value.split())


def normalized_tags(tags):
    if tags is None:
        return ()
    if isinstance(tags, str):
        tags = (tags,)
    try:
        values = tuple(tags)
    except TypeError as error:
        raise SemanticMemoryValidationError("tags must be an iterable of strings") from error
    result = []
    for tag in values:
        clean = normalized_text(tag, "tag").casefold()
        if clean not in result:
            result.append(clean)
    return tuple(result)


def normalized_score(value, field_name):
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
        raise SemanticMemoryValidationError(f"{field_name} must be a number between 0 and 1")
    return float(value)


def normalized_metadata(metadata):
    if metadata is None:
        return {}
    if not isinstance(metadata, dict):
        raise SemanticMemoryValidationError("metadata must be a dictionary")
    return dict(metadata)
