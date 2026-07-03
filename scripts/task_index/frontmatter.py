"""タスクファイルのfrontmatterとH1タイトルのパース。

frontmatterは `---` で挟まれたYAMLサブセット(`key: value` と `key: [a, b]` のみ)。
このリポジトリのタスクテンプレート(docs/tasks/_template.md)が生成する形に限定して
厳格にパースする。想定外の形は黙って通さず TaskParseError にする。
"""

from __future__ import annotations

import re

from .models import (
    REQUIRED_FRONTMATTER_KEYS,
    VALID_STATUSES,
    TaskEntry,
    TaskParseError,
)

_FENCE = "---"
# H1見出し。"# T-002: 開発環境scaffolding..." の形を想定。
_H1_RE = re.compile(r"^#\s+(?P<h1>.+?)\s*$")
# タイトル列で除去するプレフィックス "T-NNN: "(全角/半角コロンは半角のみ想定)。
_TITLE_PREFIX_RE = re.compile(r"^(?P<task_id>T-\d{3,}):\s*(?P<title>.+)$")


def _split_frontmatter(path: str, text: str) -> tuple[list[str], list[str]]:
    """本文を (frontmatter行, 本文行) に分割する。

    先頭行が `---` で始まり、次の `---` で閉じる形のみ許容する。
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != _FENCE:
        raise TaskParseError(path, "先頭行が frontmatter fence (---) ではない")
    for i in range(1, len(lines)):
        if lines[i].strip() == _FENCE:
            return lines[1:i], lines[i + 1 :]
    raise TaskParseError(path, "frontmatter の閉じfence (---) が見つからない")


def _parse_scalar_or_list(raw: str) -> str | tuple[str, ...]:
    """frontmatter値をスカラ文字列または文字列tupleへ変換する。

    `[a, b]` はlist、空文字はNone相当の空、それ以外はスカラ。
    """
    value = raw.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return ()
        return tuple(item.strip() for item in inner.split(","))
    return value


def _parse_frontmatter_fields(path: str, fm_lines: list[str]) -> dict[str, object]:
    """frontmatter行を key -> 値(スカラ or tuple) の辞書に変換する。"""
    fields: dict[str, object] = {}
    for line in fm_lines:
        if not line.strip():
            continue
        if ":" not in line:
            raise TaskParseError(path, f"frontmatter行に ':' がない: {line!r}")
        key, _, raw = line.partition(":")
        key = key.strip()
        if not key:
            raise TaskParseError(path, f"frontmatter行のキーが空: {line!r}")
        fields[key] = _parse_scalar_or_list(raw)
    return fields


def _extract_h1(path: str, body_lines: list[str]) -> str:
    """本文から最初のH1(# ...)を取り出す。"""
    for line in body_lines:
        match = _H1_RE.match(line)
        if match:
            return match.group("h1").strip()
    raise TaskParseError(path, "H1見出し (# ...) が本文に見つからない")


def _title_from_h1(path: str, h1: str, task_id: str) -> str:
    """H1から表示タイトルを得る。"T-NNN: タイトル" の "T-NNN: " を除く。"""
    match = _TITLE_PREFIX_RE.match(h1)
    if not match:
        raise TaskParseError(path, f"H1が 'T-NNN: タイトル' 形式でない: {h1!r}")
    if match.group("task_id") != task_id:
        raise TaskParseError(
            path,
            f"H1のtask_id({match.group('task_id')})とfrontmatter({task_id})が不一致",
        )
    return match.group("title").strip()


def _require_scalar(path: str, fields: dict[str, object], key: str) -> str:
    """必須スカラキーを取り出す。欠落・空・list型はエラー。"""
    if key not in fields:
        raise TaskParseError(path, f"必須frontmatterキー {key} が欠落")
    value = fields[key]
    if isinstance(value, tuple):
        raise TaskParseError(path, f"{key} はスカラであるべきだがlist")
    if not value:
        raise TaskParseError(path, f"{key} が空")
    return value


def parse_task_file(path: str, filename: str, text: str) -> TaskEntry:
    """タスクファイルの中身から TaskEntry を作る。

    Args:
        path: エラーメッセージ用のパス表示(相対推奨)。
        filename: _indexのリンク先に使うbasename。
        text: タスクファイル全文。

    Raises:
        TaskParseError: frontmatter/H1が想定形でない、必須キー欠落、不正status等。
    """
    fm_lines, body_lines = _split_frontmatter(path, text)
    fields = _parse_frontmatter_fields(path, fm_lines)

    for key in REQUIRED_FRONTMATTER_KEYS:
        if key not in fields:
            raise TaskParseError(path, f"必須frontmatterキー {key} が欠落")

    task_id = _require_scalar(path, fields, "task_id")
    epic = _require_scalar(path, fields, "epic")
    status = _require_scalar(path, fields, "status")
    if status not in VALID_STATUSES:
        raise TaskParseError(
            path,
            f"不正なstatus値 {status!r}(許容: {', '.join(VALID_STATUSES)})",
        )

    blocked_raw = fields.get("blocked_by", ())
    if isinstance(blocked_raw, tuple):
        blocked_by = blocked_raw
    elif blocked_raw == "":
        blocked_by = ()
    else:
        raise TaskParseError(path, "blocked_by はlist形式([T-001])または空である必要がある")

    h1 = _extract_h1(path, body_lines)
    title = _title_from_h1(path, h1, task_id)

    return TaskEntry(
        task_id=task_id,
        epic=epic,
        status=status,
        blocked_by=blocked_by,
        title=title,
        filename=filename,
    )
