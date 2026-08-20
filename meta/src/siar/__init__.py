# Vixen Intelligence c.2026
"""The SIaR Framework as one installable thing.

This package holds no product. It exists so that a client runs one install line instead of two,
and so that the manual for the download as a whole has a command that opens it. What it carries is
a dependency on each half and, in ``pyproject.toml``, their console scripts under its own name —
see :mod:`siar.cli` for why that second part is what makes the single install work.

Nothing here is compiled. There is nothing in it to protect: the two packages that hold the
product are native extensions built by ``siar-dist/tools/build_release.py``, and this is the
seam that names them.
"""
from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__"]
