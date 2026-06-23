"""Thin entry point for the MemHub reference CLI.

The implementation lives in a single source of truth:
``skills/memhub/scripts/memhub.py``. That file is also distributed standalone
inside the MemHub Skill, so keeping one copy avoids the two drifting apart.

This module loads that script by path and re-exports its public surface, so
both ``python -m memhub_cli`` and the ``memhub`` console script keep working.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SKILL_SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "memhub"
    / "scripts"
    / "memhub.py"
)


def _load_impl():
    if not _SKILL_SCRIPT.exists():
        raise SystemExit(
            f"MemHub implementation not found at {_SKILL_SCRIPT}. "
            "Run from a full checkout that includes skills/memhub/scripts/memhub.py."
        )
    spec = importlib.util.spec_from_file_location("memhub_cli._impl", _SKILL_SCRIPT)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Cannot load MemHub implementation from {_SKILL_SCRIPT}.")
    module = importlib.util.module_from_spec(spec)
    sys.modules["memhub_cli._impl"] = module
    spec.loader.exec_module(module)
    return module


_impl = _load_impl()
# Re-export the public surface so `from memhub_cli.__main__ import main` and
# direct attribute access continue to work for tests and importers.
globals().update({k: v for k, v in vars(_impl).items() if not k.startswith("__")})

main = _impl.main


if __name__ == "__main__":
    raise SystemExit(main())
