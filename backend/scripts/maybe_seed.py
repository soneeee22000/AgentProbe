"""Conditionally run the demo seed at startup.

Reads ``SEED_DEMO_ON_STARTUP`` from the environment. When set to a truthy
value (``true`` / ``1`` / ``yes``), runs the demo seed against the current
``DATABASE_URL`` so the deployed instance always has the demo runs ready
to display.

Designed to be safe to call on every boot — the underlying seed script is
idempotent (deletes the demo IDs first, then re-inserts).

Usage (typically via railway.toml startCommand):
    python -m scripts.maybe_seed
"""

from __future__ import annotations

import asyncio
import os
import sys


_TRUTHY = {"1", "true", "yes", "y", "on"}


def main() -> int:
    flag = os.getenv("SEED_DEMO_ON_STARTUP", "").strip().lower()
    if flag not in _TRUTHY:
        print("[maybe_seed] SEED_DEMO_ON_STARTUP not enabled — skipping seed.")
        return 0
    try:
        from scripts.seed_demo_runs import seed
    except ImportError as exc:
        print(f"[maybe_seed] cannot import seed: {exc}", file=sys.stderr)
        return 0  # don't fail the boot — production can still run without demo data
    try:
        asyncio.run(seed())
        print("[maybe_seed] demo runs seeded.")
    except Exception as exc:  # noqa: BLE001
        print(f"[maybe_seed] seed failed (continuing boot): {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
