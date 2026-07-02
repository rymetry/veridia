"""Parse unified git diffs into changed-file candidates."""

from __future__ import annotations

from dataclasses import dataclass, replace

NULL_PATH = "/dev/null"
DIFF_PREFIX = "diff --git "
NEW_FILE_PREFIX = "new file mode "
DELETED_FILE_PREFIX = "deleted file mode "
RENAME_FROM_PREFIX = "rename from "
RENAME_TO_PREFIX = "rename to "
OLD_PATH_PREFIX = "--- "
NEW_PATH_PREFIX = "+++ "
ADDED_LINE_PREFIX = "+"
DELETED_LINE_PREFIX = "-"


@dataclass(frozen=True)
class ChangedFile:
    """One file entry parsed from a unified git diff."""

    path: str
    change_type: str
    lines_added: int
    lines_deleted: int
    old_path: str | None = None


@dataclass(frozen=True)
class _FileBuilder:
    old_path: str | None = None
    new_path: str | None = None
    change_type: str = "modified"
    lines_added: int = 0
    lines_deleted: int = 0
    rename_from: str | None = None
    rename_to: str | None = None


def parse_unified_diff(diff_text: str) -> tuple[ChangedFile, ...]:
    """Return changed files from a git unified diff in input order."""
    entries: list[ChangedFile] = []
    current: _FileBuilder | None = None

    for line in diff_text.splitlines():
        if line.startswith(DIFF_PREFIX):
            if current is not None:
                entries.append(_finalize(current))
            current = _builder_from_diff_header(line)
            continue

        if current is None:
            continue

        current = _consume_file_line(current, line)

    if current is not None:
        entries.append(_finalize(current))

    if not entries:
        raise ValueError("diff did not contain any 'diff --git' file entries")
    return tuple(entries)


def _builder_from_diff_header(line: str) -> _FileBuilder:
    parts = line.split()
    if len(parts) < 4:
        raise ValueError(f"malformed diff header: {line}")
    return _FileBuilder(old_path=_strip_git_prefix(parts[2]), new_path=_strip_git_prefix(parts[3]))


def _consume_file_line(builder: _FileBuilder, line: str) -> _FileBuilder:
    if line.startswith(NEW_FILE_PREFIX):
        return replace(builder, change_type="added")
    if line.startswith(DELETED_FILE_PREFIX):
        return replace(builder, change_type="deleted")
    if line.startswith(RENAME_FROM_PREFIX):
        return replace(builder, change_type="renamed", rename_from=line[len(RENAME_FROM_PREFIX) :])
    if line.startswith(RENAME_TO_PREFIX):
        return replace(builder, change_type="renamed", rename_to=line[len(RENAME_TO_PREFIX) :])
    if line.startswith(OLD_PATH_PREFIX):
        old_path = line[len(OLD_PATH_PREFIX) :]
        return replace(builder, old_path=_strip_git_prefix(old_path))
    if line.startswith(NEW_PATH_PREFIX):
        new_path = line[len(NEW_PATH_PREFIX) :]
        return replace(builder, new_path=_strip_git_prefix(new_path))
    if _is_added_content_line(line):
        return replace(builder, lines_added=builder.lines_added + 1)
    if _is_deleted_content_line(line):
        return replace(builder, lines_deleted=builder.lines_deleted + 1)
    return builder


def _finalize(builder: _FileBuilder) -> ChangedFile:
    path = _effective_path(builder)
    old_path = builder.rename_from or (
        builder.old_path if builder.change_type in {"deleted", "renamed"} else None
    )
    change_type = builder.change_type
    if builder.old_path == NULL_PATH:
        change_type = "added"
    elif builder.new_path == NULL_PATH:
        change_type = "deleted"

    return ChangedFile(
        path=path,
        change_type=change_type,
        lines_added=builder.lines_added,
        lines_deleted=builder.lines_deleted,
        old_path=old_path if old_path != path else None,
    )


def _effective_path(builder: _FileBuilder) -> str:
    path = builder.rename_to or builder.new_path
    if path and path != NULL_PATH:
        return path
    path = builder.rename_from or builder.old_path
    if path and path != NULL_PATH:
        return path
    raise ValueError("diff file entry did not contain a usable path")


def _is_added_content_line(line: str) -> bool:
    return line.startswith(ADDED_LINE_PREFIX) and not line.startswith(NEW_PATH_PREFIX)


def _is_deleted_content_line(line: str) -> bool:
    return line.startswith(DELETED_LINE_PREFIX) and not line.startswith(OLD_PATH_PREFIX)


def _strip_git_prefix(path: str) -> str:
    if path == NULL_PATH:
        return path
    if path.startswith("a/") or path.startswith("b/"):
        return path[2:]
    return path
