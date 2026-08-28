# Vixen Intelligence c.2026
"""The console scripts this download installs, each with one guard in front of it.

``pyproject.toml`` used to name the programs' own entry points directly, and the comment there
made a point of it: nothing wrapped, nothing re-implemented, the same targets those wheels declare
themselves. That is still true of everything after the first line of each function here — the
delegation is an import and a call, and every argument, exit status and stream belongs to the
program being run.

What changed is that a native extension can fail to *load*, and when it does the failure is the
dynamic loader's, arriving as a traceback about a versioned symbol in a library the client has
never heard of. A generated console script imports its target at module scope, so there is nowhere
to catch that unless something sits in front. This is that something, and it is the smallest thing
that can be: check the exception, print :func:`siar.glibc.explain`'s account of it, exit 1.

**This is the second of two guards, and usually not the one that runs.** Each product wheel carries
its own launcher, written in by ``build_release.py``, because these entry points do not reliably
survive an install: every wheel here declares a ``siar-db``, all of them are installed into one
environment, and which lands last is not ordered — ``uv tool install`` was observed writing the
siar-db wheel's script over this package's, leaving the guard installed and unreachable. That is
what put the guard in the wheels; this stays because the race runs both ways and a second identical
guard costs nothing.
"""
from __future__ import annotations

import sys
from typing import Callable

__all__ = ["siar_app", "siar_build", "siar_db"]


def _guarded(program: str, target: Callable[[], Callable]) -> int:
    """Run one program, turning a C-library mismatch into an explanation.

    Args:
        program: The command's name, for the message.
        target: A callable returning the program's own ``main``. A callable rather than the
            function itself because importing it is the thing that can fail, and it has to fail
            inside this try.

    Returns:
        Whatever the program returned, or 1 if it could not be loaded.
    """
    try:
        main = target()
    except ImportError as exc:
        from siar import glibc

        if not glibc.is_glibc_error(exc):
            raise
        print(glibc.explain(exc, program), file=sys.stderr)
        return 1
    return main()


def siar_app() -> int:
    """``siar-app`` — run models."""
    def load():
        from siarapp.cli.main import main
        return main
    return _guarded("siar-app", load)


def siar_build() -> int:
    """``siar-build`` — breed them."""
    def load():
        from siarbuild.cli import main
        return main
    return _guarded("siar-build", load)


def siar_db() -> int:
    """``siar-db`` — scan a corpus into a queryable structure database."""
    def load():
        from siardb.cli.main import main
        return main
    return _guarded("siar-db", load)
