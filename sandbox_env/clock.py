"""Deterministic clock helper for Phase 0 sandbox execution."""

from __future__ import annotations

import os
from datetime import UTC, datetime

from sandbox_env.errors import SandboxEnvError

FIXED_NOW_ENV_VAR = "VERIDIA_FIXED_NOW"


def now() -> datetime:
    """Return fixed UTC time from VERIDIA_FIXED_NOW, or the real UTC time."""

    fixed_now = os.environ.get(FIXED_NOW_ENV_VAR)
    if fixed_now is None:
        return datetime.now(UTC)
    return parse_fixed_now(fixed_now)


def parse_fixed_now(value: str) -> datetime:
    """Parse a VERIDIA_FIXED_NOW value as a timezone-aware UTC datetime."""

    normalized = value.removesuffix("Z") + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise SandboxEnvError(
            f"invalid {FIXED_NOW_ENV_VAR}={value!r}: expected ISO 8601 UTC datetime"
        ) from exc

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SandboxEnvError(
            f"invalid {FIXED_NOW_ENV_VAR}={value!r}: expected timezone-aware UTC datetime"
        )
    if parsed.utcoffset() != UTC.utcoffset(parsed):
        raise SandboxEnvError(f"invalid {FIXED_NOW_ENV_VAR}={value!r}: expected UTC offset")

    return parsed.astimezone(UTC)
