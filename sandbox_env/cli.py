"""Command line interface for Phase 0 sandbox environments."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from sandbox_env.errors import SandboxEnvError
from sandbox_env.hashing import state_hash
from sandbox_env.lifecycle import create, destroy, reset

EXIT_OK = 0
EXIT_INPUT_ERROR = 2


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except SandboxEnvError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_INPUT_ERROR


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage a Phase 0 sandbox environment.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    _add_root_command(subparsers, "create", _create, "Create a new sandbox root.")
    _add_root_command(subparsers, "destroy", _destroy, "Destroy a sandbox root.")
    _add_root_command(subparsers, "reset", _reset, "Delete and recreate a sandbox root.")
    _add_root_command(
        subparsers,
        "state-hash",
        _state_hash,
        "Print the normalized sandbox state hash.",
    )

    return parser


def _add_root_command(
    subparsers: argparse._SubParsersAction,
    name: str,
    func: Callable[[argparse.Namespace], int],
    help_text: str,
) -> None:
    subparser = subparsers.add_parser(name, help=help_text, description=help_text)
    subparser.add_argument("root", type=Path, help="Sandbox root path")
    subparser.set_defaults(func=func)


def _create(args: argparse.Namespace) -> int:
    env = create(args.root)
    print(f"created: {env.root}")
    return EXIT_OK


def _destroy(args: argparse.Namespace) -> int:
    destroy(args.root)
    print(f"destroyed: {args.root}")
    return EXIT_OK


def _reset(args: argparse.Namespace) -> int:
    env = reset(args.root)
    print(f"reset: {env.root}")
    return EXIT_OK


def _state_hash(args: argparse.Namespace) -> int:
    print(state_hash(args.root))
    return EXIT_OK
