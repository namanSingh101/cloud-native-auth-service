from dataclasses import dataclass
from pathlib import Path

from app.core.global_error import BusinessRuleViolation

@dataclass(frozen=True)
class FileTypePolicy:
    extensions: tuple[str, ...]
    max_bytes: int


FILE_TYPE_POLICIES: dict[str, FileTypePolicy] = {
    "image/jpeg": FileTypePolicy(
        extensions=(".jpg", ".jpeg"),
        max_bytes=5 * 1024 * 1024,   # 5 MB
    ),
    "image/png": FileTypePolicy(
        extensions=(".png",),
        max_bytes=5 * 1024 * 1024,
    ),
    "application/pdf": FileTypePolicy(
        extensions=(".pdf",),
        max_bytes=20 * 1024 * 1024,  # 20 MB
    ),
}

ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset(FILE_TYPE_POLICIES.keys())

EXTENSION_MAP: dict[str, str] = {
    ext.lower(): content_type
    for content_type, policy in FILE_TYPE_POLICIES.items()
    for ext in policy.extensions
}


def get_policy_for_file(filename: str, content_type: str) -> FileTypePolicy:
    """
    Validate filename extension and content type match policy.
    Returns the applicable FileTypePolicy if valid.
    """
    bare_name = Path(filename).name.strip()

    if not bare_name:
        raise ValueError("invalid filename")

    suffix = Path(bare_name).suffix.lower()

    if not suffix:
        raise ValueError("file must have an extension")

    if suffix not in EXTENSION_MAP:
        raise ValueError("unsupported file extension")

    normalized_content_type = content_type.split(";")[0].strip().lower()

    expected_content_type = EXTENSION_MAP[suffix]

    if expected_content_type != normalized_content_type:
        raise ValueError("content type does not match file extension")

    return FILE_TYPE_POLICIES[normalized_content_type]
