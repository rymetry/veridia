"""Parse unified git diffs into changed-file candidates."""

from __future__ import annotations

from dataclasses import dataclass, replace
from string import hexdigits

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
HUNK_PREFIX = "@@"


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
    in_hunk: bool = False


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
    paths = _split_diff_header_paths(line[len(DIFF_PREFIX) :])
    return _FileBuilder(
        old_path=_strip_git_prefix(_decode_git_path(paths[0])),
        new_path=_strip_git_prefix(_decode_git_path(paths[1])),
    )


def _consume_file_line(builder: _FileBuilder, line: str) -> _FileBuilder:
    if line.startswith(HUNK_PREFIX):
        return replace(builder, in_hunk=True)
    if builder.in_hunk:
        if line.startswith(ADDED_LINE_PREFIX):
            return replace(builder, lines_added=builder.lines_added + 1)
        if line.startswith(DELETED_LINE_PREFIX):
            return replace(builder, lines_deleted=builder.lines_deleted + 1)
        return builder

    if line.startswith(NEW_FILE_PREFIX):
        return replace(builder, change_type="added")
    if line.startswith(DELETED_FILE_PREFIX):
        return replace(builder, change_type="deleted")
    if line.startswith(RENAME_FROM_PREFIX):
        return replace(
            builder,
            change_type="renamed",
            rename_from=_decode_git_path(line[len(RENAME_FROM_PREFIX) :]),
        )
    if line.startswith(RENAME_TO_PREFIX):
        return replace(
            builder,
            change_type="renamed",
            rename_to=_decode_git_path(line[len(RENAME_TO_PREFIX) :]),
        )
    if line.startswith(OLD_PATH_PREFIX):
        old_path = line[len(OLD_PATH_PREFIX) :]
        return replace(builder, old_path=_strip_git_prefix(_decode_git_path(old_path)))
    if line.startswith(NEW_PATH_PREFIX):
        new_path = line[len(NEW_PATH_PREFIX) :]
        return replace(builder, new_path=_strip_git_prefix(_decode_git_path(new_path)))
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


def _strip_git_prefix(path: str) -> str:
    if path == NULL_PATH:
        return path
    if path.startswith("a/") or path.startswith("b/"):
        return path[2:]
    return path


def _split_diff_header_paths(value: str) -> tuple[str, str]:
    rest = value.strip()
    if not rest:
        raise ValueError(f"malformed diff header: missing paths: {value!r}")

    first, remaining = _read_git_path_token(rest)
    second, trailing = _read_git_path_token(remaining.lstrip())
    if trailing.strip():
        raise ValueError(f"malformed diff header path list: {value}")
    return (first, second)


def _read_git_path_token(value: str) -> tuple[str, str]:
    if not value:
        raise ValueError("malformed diff header: missing path")
    if value.startswith('"'):
        end_index = _quoted_token_end(value)
        return value[:end_index], value[end_index:]

    separator = " b/"
    if value.startswith("a/") and separator in value:
        index = value.rfind(separator)
        return value[:index], value[index + 1 :]
    if value.startswith("b/"):
        return value, ""

    parts = value.split(maxsplit=1)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def _quoted_token_end(value: str) -> int:
    escaped = False
    for index, char in enumerate(value[1:], start=1):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            return index + 1
    raise ValueError(f"unterminated quoted git path: {value}")


def _decode_git_path(raw_path: str) -> str:
    token = raw_path.strip()
    if not token.startswith('"'):
        return _path_without_timestamp(token)
    if len(token) < 2 or not token.endswith('"'):
        raise ValueError(f"malformed quoted git path: {raw_path}")
    return _decode_c_quoted_path(token[1:-1])


def _path_without_timestamp(path: str) -> str:
    if "\t" in path:
        return path.split("\t", 1)[0]
    return path


def _decode_c_quoted_path(value: str) -> str:
    output = bytearray()
    index = 0
    while index < len(value):
        char = value[index]
        if char != "\\":
            output.extend(char.encode("utf-8"))
            index += 1
            continue

        if index + 1 >= len(value):
            raise ValueError("invalid trailing escape in quoted git path")
        next_char = value[index + 1]
        if next_char in {'"', "\\"}:
            output.extend(next_char.encode("utf-8"))
            index += 2
            continue
        if next_char in "abfnrtv":
            output.extend(
                {
                    "a": b"\a",
                    "b": b"\b",
                    "f": b"\f",
                    "n": b"\n",
                    "r": b"\r",
                    "t": b"\t",
                    "v": b"\v",
                }[next_char]
            )
            index += 2
            continue
        if next_char in hexdigits and next_char not in "89ABCDEFabcdef":
            octal = value[index + 1 : index + 4]
            if len(octal) != 3 or any(char not in "01234567" for char in octal):
                raise ValueError(f"invalid octal escape in quoted git path: \\{octal}")
            output.append(int(octal, 8))
            index += 4
            continue
        raise ValueError(f"unsupported escape in quoted git path: \\{next_char}")

    try:
        return output.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"quoted git path is not valid UTF-8: {exc}") from exc
