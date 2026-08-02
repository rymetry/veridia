"""Run W1 against one change: ChangeSet JSON in, stored RunRecord out.

    uv run python -m source_connector --repo . --base HEAD~1 --head HEAD --output change.json
    uv run python qa-skills/source-grounding/scripts/run_skill.py change.json

This calls a real LLM through the CLI backend (ADR-0005) and costs money, so it is an
explicit entry point rather than anything the test suite reaches. `pytest` exercises the
same path with `FakeLLMClient`, which is never selectable from the environment
(ADR-0005 Decision 3).

`trust_level` comes from the ChangeSet — that is, from the ingestion configuration —
and is written over whatever the model produces (ADR-0009 Decision 2).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# The repo is `package = false` (pyproject), so a standalone script has to put the
# repo root on the path itself. Tests reach these modules through pytest's pythonpath.
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from run_store import RunStore  # noqa: E402
from skill_runner import (  # noqa: E402
    ClaudeCliLLMClient,
    QaSkillSource,
    SkillRunner,
    SkillRunnerError,
)
from skill_runner.runner import default_prompt_data  # noqa: E402
from trace_store import TraceStore  # noqa: E402

SKILL = "source-grounding"
TRUST_LEVEL_FIELD = "trust_level"
EXIT_OK = 0
EXIT_ERROR = 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the source-grounding skill (W1).")
    parser.add_argument("change_set", type=Path, help="ChangeSet JSON from source_connector")
    parser.add_argument("--agent", default="source-grounding-cli", help="Recorded as created_by")
    parser.add_argument("--store-root", type=Path, default=Path(".veridia/store"))
    args = parser.parse_args(argv)

    try:
        change = json.loads(args.change_set.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: failed to read {args.change_set}: {exc}", file=sys.stderr)
        return EXIT_ERROR

    source_refs = change.get("source_refs") or []
    if not source_refs:
        print("error: the ChangeSet declares no source_refs", file=sys.stderr)
        return EXIT_ERROR

    runner = SkillRunner(
        llm_client=ClaudeCliLLMClient(),
        run_store=RunStore.open(args.store_root / "runs"),
        trace_store=TraceStore.open(args.store_root / "trace"),
        skill_source=QaSkillSource(),
    )
    try:
        result = runner.run(
            SKILL,
            input_text=default_prompt_data(change),
            source_refs=source_refs,
            agent=args.agent,
            authoritative_fields=(
                {TRUST_LEVEL_FIELD: change[TRUST_LEVEL_FIELD]}
                if TRUST_LEVEL_FIELD in change
                else None
            ),
        )
    except (SkillRunnerError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    print(f"stored {result.run_id}: {result.record_path}")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
