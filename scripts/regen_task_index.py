#!/usr/bin/env python3
"""CLIエントリポイント: docs/tasks/<phase>/_index.md を再生成する。

使用例:
    uv run python scripts/regen_task_index.py docs/tasks/phase-0
    uv run python scripts/regen_task_index.py docs/tasks/phase-0 --check
"""

from __future__ import annotations

import sys

from task_index.cli import main

if __name__ == "__main__":
    sys.exit(main())
