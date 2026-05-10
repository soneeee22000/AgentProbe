"""Conditionally run the demo seed at startup.

Reads ``SEED_DEMO_ON_STARTUP`` from the environment. When set to a truthy
value (``true`` / ``1`` / ``yes``), runs the demo seed against the current
``DATABASE_URL`` so the deployed instance always has the demo runs ready
to display.

Designed to be safe to call on every boot:

* The underlying seed script is idempotent (deletes the demo IDs first,
  then re-inserts).
* Any failure during the seed is logged with a full traceback but does
  NOT crash the boot — the API must come up even if the demo data
  doesn't, otherwise a single bad seed wedges all of production.

Every code path prints exactly one ``[maybe_seed]`` line (success, skip,
or failure) so Railway/Render deploy logs always show what happened. Use
``flush=True`` on every print so the lines reach the log shipper before
``uvicorn`` takes over and floods the buffer.

Usage (typically via railway.toml startCommand):
    python -m scripts.maybe_seed
"""

from __future__ import annotations

import asyncio
import os
import sys
import traceback

_TRUTHY = {"1", "true", "yes", "y", "on"}


def main() -> int:
    raw_flag = os.getenv("SEED_DEMO_ON_STARTUP", "")
    flag = raw_flag.strip().lower()
    db_hint = _redacted_database_hint()

    if flag not in _TRUTHY:
        print(
            f"[maybe_seed] SEED_DEMO_ON_STARTUP={raw_flag!r} not truthy "
            f"(expected one of {sorted(_TRUTHY)}) — skipping seed. "
            f"DATABASE_URL={db_hint}",
            flush=True,
        )
        return 0

    print(
        f"[maybe_seed] SEED_DEMO_ON_STARTUP={raw_flag!r} is truthy — "
        f"running seed against DATABASE_URL={db_hint}",
        flush=True,
    )

    try:
        from scripts.seed_demo_runs import seed
    except ImportError as exc:
        print(
            f"[maybe_seed] cannot import seed module: {exc}. "
            f"Boot will continue without demo data.",
            file=sys.stderr,
            flush=True,
        )
        traceback.print_exc()
        sys.stderr.flush()
        return 0

    try:
        asyncio.run(seed())
    except Exception as exc:  # noqa: BLE001
        print(
            f"[maybe_seed] seed FAILED: {type(exc).__name__}: {exc}. "
            f"Boot will continue without demo data — check the traceback below.",
            file=sys.stderr,
            flush=True,
        )
        traceback.print_exc()
        sys.stderr.flush()
        return 0

    print("[maybe_seed] demo runs seeded.", flush=True)
    return 0


def _redacted_database_hint() -> str:
    """Return a safe-to-log fingerprint of DATABASE_URL.

    Shows only the scheme + host so we can confirm we're talking to the
    right database, without leaking the password into deploy logs.
    """
    url = os.getenv("DATABASE_URL", "")
    if not url:
        return "<unset, defaulting to local sqlite>"
    # Strip credentials: scheme://user:pass@host/db -> scheme://***@host/db
    try:
        scheme, rest = url.split("://", 1)
    except ValueError:
        return "<malformed>"
    if "@" in rest:
        host_and_path = rest.split("@", 1)[1]
    else:
        host_and_path = rest
    return f"{scheme}://***@{host_and_path}"


if __name__ == "__main__":
    raise SystemExit(main())
