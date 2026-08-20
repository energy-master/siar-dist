# Vixen Intelligence c.2026
"""``siar`` — the front door of a download that installs two programs.

Two commands, and neither of them does any work on audio. ``siar readme`` puts the manual for the
download *as a whole* in a browser, and ``siar version`` says which halves are actually installed
and at what version. Everything else a client came for is ``siar-app`` and ``siar-build``, which
this distribution puts on the PATH alongside it.

**Why the manual is not a file in this package.** ``pyproject.toml`` names the repository's
README as the project's long description, so a wheel already carries the whole of it in its
metadata; :func:`readme_markdown` reads it back from there. One copy, at the repository root, and
no build step keeping a second one in step with it. This is siar-build's arrangement carried
across, for the same reason it was made there.

**Why the renderer is borrowed.** ``siarbuild.docs.to_html`` is a dependency of this package by
construction, and it already renders the constructs these READMEs use — including the ``<details>``
blocks that are load-bearing in the install sections. A second Markdown implementation living here
would be a second thing to keep true, and the three manuals would start to look like three
products. Where it cannot be imported the command still works: the Markdown goes to stdout with a
sentence saying why, rather than a traceback about an import a client never made.
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile

__all__ = ["DISTRIBUTIONS", "main", "readme_markdown", "render_page"]

#: What a full install of this download consists of, in the order ``siar version`` reports them.
#: brahma-intelligence is included because it is siar-build's engine and the one dependency a
#: client never asked for by name — when an install goes wrong it is usually the missing row.
DISTRIBUTIONS = ("siar", "siar-app", "siar-build", "brahma-intelligence")

#: The page the rendered manual is written into. Deliberately plain and deliberately inline: this
#: is opened over ``file://`` on a machine that may have no network at all, so a stylesheet from
#: anywhere else would be a blank page on exactly the machines this command exists for.
_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The SIaR Framework</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ max-width: 54rem; margin: 3rem auto; padding: 0 1.5rem;
         font: 16px/1.65 system-ui, -apple-system, "Segoe UI", sans-serif; }}
  h1, h2, h3 {{ line-height: 1.25; margin-top: 2.2rem; }}
  code {{ font-size: 0.92em; }}
  pre {{ overflow-x: auto; padding: 0.9rem 1rem; border-radius: 6px;
        background: rgba(127, 127, 127, 0.12); }}
  table {{ border-collapse: collapse; }}
  th, td {{ text-align: left; padding: 0.35rem 0.9rem 0.35rem 0;
           border-bottom: 1px solid rgba(127, 127, 127, 0.35); }}
  blockquote {{ margin-left: 0; padding-left: 1rem;
                border-left: 3px solid rgba(127, 127, 127, 0.4); }}
</style></head><body>
{body}
</body></html>
"""


def readme_markdown() -> str:
    """The download's README, from the checkout if there is one, else this wheel's metadata.

    The file wins when it exists, and the order matters: an installed distribution keeps serving
    the long description it was built with, so asking metadata first would show somebody editing
    the README whatever it said when they last built — stale documentation presented as current,
    which is worse than none.

    A real install has no checkout beside it and falls through to the metadata, which is why this
    works from a tool install with nothing cloned anywhere.

    Returns:
        The raw Markdown, or an empty string if neither source has it.
    """
    # meta/src/siar/cli.py -> meta/src/siar -> meta/src -> meta -> the repository root. The README
    # lives at the root, one above this package's own project directory, so both are tried.
    here = os.path.dirname(os.path.abspath(__file__))
    for _ in range(4):
        here = os.path.dirname(here)
        candidate = os.path.join(here, "README.md")
        if os.path.isfile(candidate):
            try:
                with open(candidate, encoding="utf-8") as fh:
                    return fh.read()
            except OSError:
                break  # unreadable for some reason — the metadata copy is still worth trying

    try:
        from importlib.metadata import metadata

        md = metadata("siar")
        text = md.get_payload() if hasattr(md, "get_payload") else None
        if not text:
            text = md.get("Description") or ""
        if text and text.strip():
            return text
    except Exception:  # noqa: BLE001 - not installed, or metadata without a description
        pass
    return ""


def render_page(markdown: str) -> str:
    """The manual as one self-contained HTML page.

    Args:
        markdown: The README text.

    Returns:
        A complete document.

    Raises:
        ImportError: If siar-build is not installed, so its renderer cannot be borrowed. The
            caller is expected to fall back to printing the Markdown rather than fail.
    """
    from siarbuild.docs import to_html

    return _PAGE.format(body=to_html(markdown))


def _cmd_readme(args: argparse.Namespace) -> int:
    """``siar readme`` — open the manual in a browser, or print it.

    Args:
        args: Parsed arguments; ``--text`` writes Markdown to stdout instead.

    Returns:
        A process exit status.
    """
    markdown = readme_markdown()
    if not markdown.strip():
        print("error: this install carries no README — neither a checkout beside it nor a long\n"
              "       description in its metadata. Reinstall from the published wheel.",
              file=sys.stderr)
        return 1

    if args.text:
        sys.stdout.write(markdown)
        return 0

    try:
        page = render_page(markdown)
    except ImportError:
        sys.stdout.write(markdown)
        print("\n(siar-build is not installed, so the manual could not be rendered. The Markdown\n"
              " is above; `siar readme --text` prints it without this note.)", file=sys.stderr)
        return 0

    try:
        directory = tempfile.mkdtemp(prefix="siar-readme-")
        path = os.path.join(directory, "siar-readme.html")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(page)
    except OSError as e:
        print(f"error: could not write the rendered manual: {e}", file=sys.stderr)
        return 1

    from siarbuild.docs import open_path

    if not open_path(path):
        # The expected branch on a survey box or over ssh, not an edge case.
        print(f"No browser to open here. The rendered manual is at:\n  {path}")
    return 0


def _cmd_version(args: argparse.Namespace) -> int:
    """``siar version`` — the four distributions, and whether each one is present.

    Args:
        args: Parsed arguments. Unused.

    Returns:
        ``0`` when the install is complete, ``1`` when a piece of it is missing — so a support
        script can test the exit status instead of reading the table.
    """
    from importlib.metadata import PackageNotFoundError, version

    missing = 0
    for dist in DISTRIBUTIONS:
        try:
            print(f"  {dist:<22}{version(dist)}")
        except PackageNotFoundError:
            print(f"  {dist:<22}not installed")
            missing += 1
    if missing:
        print(f"\n{missing} of {len(DISTRIBUTIONS)} missing. Install the whole download with:\n"
              "  uv tool install --python 3.13 <the siar wheel's URL>", file=sys.stderr)
    return 1 if missing else 0


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``siar`` command.

    Args:
        argv: Arguments, for tests. ``None`` reads ``sys.argv``.

    Returns:
        A process exit status.
    """
    ap = argparse.ArgumentParser(
        prog="siar",
        description="The SIaR Framework. `siar-app` runs models; `siar-build` breeds them. "
                    "This command is the manual for both, and a check on what is installed.",
    )
    sub = ap.add_subparsers(dest="command", metavar="COMMAND")

    p_readme = sub.add_parser("readme", help="open the manual in a browser, offline")
    p_readme.add_argument("--text", action="store_true",
                          help="write the Markdown to stdout instead of opening a browser")

    sub.add_parser("version", help="what is installed, and at what version")

    args = ap.parse_args(argv)
    if args.command == "readme":
        return _cmd_readme(args)
    if args.command == "version":
        return _cmd_version(args)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
