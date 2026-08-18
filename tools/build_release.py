#!/usr/bin/env python3
# Vixen Intelligence c.2026
"""Build the public siar-dist download from the current commits of siar-build and brahma_lib_py.

This repository is the only public face of a product whose two source repositories are private and
staying that way. What crosses the line is compiled: each package is put through Nuitka into a
single native extension module, and the wheels here contain that ``.so`` and no statements.

Run it, and ``dist/`` holds what a client installs::

    python3 tools/build_release.py

**Built from commits, not from your desk.** Both sources are exported with ``git archive HEAD``,
so a wheel contains what is committed and nothing else — no half-finished edit, no ignored
scratch file, no ``.git`` to mine. A dirty tree is refused; ``--allow-dirty`` builds from the
working tree instead and stamps the manifest, which is a thing to do while iterating and never
before a release.

**Why Nuitka rather than an obfuscator.** PyArmor and its relatives leave the program as
bytecode and add a runtime that unwraps it, so the plaintext exists in memory at some moment by
construction. Nuitka compiles to C and then to machine code: what is left is a shared object with
no statements in it, and reversing it yields somebody's generated C rather than our source. It
also turned out to be undemanding — brahma's 53 modules compile in thirteen seconds and pass all
161 of its own tests compiled, which is the evidence that made this the default rather than an
experiment.

**The sidecar directory, and why it is not a leak.** Nuitka gives a compiled package a synthetic
``__file__`` of ``<dir>/<package>/__init__.py`` — a path that need not exist, but *may*. Both
packages read files relative to it: siar-build loads ``template/*.tmpl`` and copies its own
``rms.py`` and ``scanner_core.py`` into every model it packages, and it copies eleven modules out
of brahma for the same reason. So each wheel ships a directory of that name beside the ``.so``
holding exactly those files, and every ``Path(__file__).parent / ...`` in either package resolves
without a line of either being changed.

Those thirteen files are readable, and that is not a concession: they are *already* shipped as
readable source inside every generated model package, by design, because a model folder has to run
on a survey machine that has siar-app and nothing else. Nothing that was hidden becomes visible.
What the directory cannot do is change which code runs — a bare directory loses to an extension
module in Python's import system, and a deliberately sabotaged copy placed there was ignored in
favour of the compiled one. It is data that happens to be spelled in Python.

**What the gate is.** :func:`leak_check` opens every finished wheel and fails on any ``.py`` that
is not on that permitted list. That is the difference between having compiled the library and
believing one has, and it runs on the artefact that ships rather than the tree it came from.

**Why the dependency is a URL.** A ``git+https://`` reference *builds from source*: pointed at
the private brahma repository it resolves for nobody, and were that repository opened it would
hand over what this script exists to withhold. An index would resolve wheels properly, but pip
cannot be told about one from ``pyproject.toml`` — only from its command line — so the documented
pip install line would break while the uv line beside it kept working. Direct URLs with
environment markers keep both commands flagless, at the price of a platform matrix written down
in one place: :data:`TARGETS`.
"""
from __future__ import annotations

import argparse
import ast
import base64
import fnmatch
import hashlib
import json
import os
import platform as _platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

DEFAULT_SIARBUILD = Path("/home/vixen/apps/siar-builder")
DEFAULT_BRAHMA = Path("/home/vixen/apps/brahma_lib_py")

#: Where ``dist/`` is served from. ``raw.githubusercontent.com`` serves committed bytes with no
#: redirect, and pip installs a wheel from a plain URL without complaint.
DEFAULT_BASE_URL = "https://raw.githubusercontent.com/energy-master/siar-dist/main/dist"

#: The one Python column this product has, and the reason there is only one: Nuitka compiles
#: against a specific CPython ABI, so a cp313 wheel loads on 3.13 and nothing else. Must match the
#: floor of siar-build's ``requires-python``; if the product moves, this moves with it.
PYTHON_TAG = "cp313"


@dataclass(frozen=True, slots=True)
class Target:
    """One platform we ship for.

    Attributes:
        wheel: The wheel platform tag, which decides which machines pip will install it on.
        marker: A PEP 508 marker selecting exactly this platform. The markers across
            :data:`TARGETS` must be mutually exclusive, or a resolver is handed two candidate URLs
            for one dependency and picks between them by rules nobody wants to depend on.
    """

    wheel: str
    marker: str


#: The shipping matrix.
#:
#: Unlike an obfuscator, Nuitka does **not** cross-build: it invokes the host C compiler against
#: the host CPython, so each row here needs a machine of that kind. That is the real cost of
#: choosing compilation, and it is stated here rather than discovered — a row with no builder is a
#: platform that silently has no wheel, and :func:`patch_siarbuild_pyproject` only writes markers
#: for what was actually built.
#:
#: ``linux_x86_64`` rather than a ``manylinux`` tag: the extension links against this box's glibc
#: and claiming manylinux compliance would be a claim nobody checked. A bare ``linux`` tag is
#: refused by package indexes and accepted from a direct URL, which is what we use. The
#: consequence is that musl distributions match this marker and fail at import; Alpine would need
#: its own row and a real index.
TARGETS: dict[str, Target] = {
    "linux-x86_64": Target(
        wheel="linux_x86_64",
        marker="sys_platform == 'linux' and platform_machine == 'x86_64'",
    ),
    "darwin-arm64": Target(
        wheel="macosx_11_0_arm64",
        marker="sys_platform == 'darwin' and platform_machine == 'arm64'",
    ),
    "darwin-x86_64": Target(
        wheel="macosx_10_9_x86_64",
        marker="sys_platform == 'darwin' and platform_machine == 'x86_64'",
    ),
    "windows-x86_64": Target(
        wheel="win_amd64",
        marker="sys_platform == 'win32' and platform_machine == 'AMD64'",
    ),
}

#: Nuitka flags shared by both packages.
#:
#: ``no_docstrings`` is the one worth explaining. Neither codebase reads ``__doc__`` at runtime —
#: checked, not assumed — and both are documented to a standard that makes the docstrings worth
#: more than the code to a reader: measured AUC figures, the failure modes each guard exists for,
#: why one approach was abandoned for another. Compiling while shipping those would be leaving the
#: commentary on the design in a binary that was built to withhold the design.
NUITKA_FLAGS = ("--python-flag=no_docstrings", "--no-pyi-file", "--remove-output")


#: Tests that cannot be run against a compiled build, with the reason each is excused.
#:
#: There is exactly one, and it is a limitation of the *technique*, not of the wheel. The test
#: proves that :func:`siarbuild.docs.readme_markdown` degrades to a sentence rather than a
#: traceback when neither a source README nor package metadata is available, and it arranges that
#: by substituting ``importlib.metadata.metadata``. Nuitka binds that at build time — verified
#: against ``from ... import``, a module attribute lookup and ``importlib.import_module``, all
#: three of which ignore the substitution once compiled — so the test cannot reach the code it is
#: about. The behaviour itself is unchanged: a genuinely absent distribution still raises
#: ``PackageNotFoundError`` into the same handler.
#:
#: Deselected by name and printed, never quietly skipped. A build that excuses a test without
#: saying so reads as a build that ran it.
UNRUNNABLE_COMPILED = (
    ("test_docs.py::test_missing_readme_is_a_sentence_not_a_traceback",
     "substitutes importlib.metadata.metadata, which Nuitka binds at build time"),
)


class BuildError(RuntimeError):
    """A stage failed. The message is meant to be the whole explanation."""


# -- shell ------------------------------------------------------------------------------------


def run(cmd: list[str], cwd: Path | None = None, env: dict | None = None) -> str:
    """Run a command, or raise with both of its streams.

    Args:
        cmd: Argument vector.
        cwd: Working directory.
        env: Extra environment, merged over the current one.

    Returns:
        Captured stdout.

    Raises:
        BuildError: On a non-zero exit. The output is the point, so it travels with the error.
    """
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                          env={**os.environ, **(env or {})})
    if proc.returncode != 0:
        raise BuildError(f"{' '.join(cmd)}\n  exit {proc.returncode}\n"
                         f"{proc.stdout.strip()}\n{proc.stderr.strip()}")
    return proc.stdout


# -- sources ----------------------------------------------------------------------------------


@dataclass(slots=True)
class Source:
    """An exported tree and the commit it came from.

    Attributes:
        name: Label, for logs and the manifest.
        path: The exported tree.
        commit: Full sha of ``HEAD`` in the origin repository.
        dirty: Whether that repository had uncommitted changes. Recorded rather than merely
            refused, so a manifest can always be asked whether it describes a real commit.
    """

    name: str
    path: Path
    commit: str
    dirty: bool


def export(repo: Path, dest: Path, name: str, allow_dirty: bool) -> Source:
    """Export a repository's committed tree, or its working tree under protest.

    ``git archive HEAD`` rather than a copy, because it is defined to emit exactly the tracked,
    committed content. What ships is then a function of the sha, which is the only claim the
    manifest can make honestly.

    Args:
        repo: The source repository.
        dest: Directory to create and fill.
        name: Label for messages.
        allow_dirty: Copy the tracked working tree instead, when the repository is dirty.

    Returns:
        The exported :class:`Source`.

    Raises:
        BuildError: If ``repo`` is not a git repository, or is dirty and ``allow_dirty`` is unset.
    """
    if not (repo / ".git").exists():
        raise BuildError(f"{name}: {repo} is not a git repository")

    commit = run(["git", "-C", str(repo), "rev-parse", "HEAD"]).strip()
    status = run(["git", "-C", str(repo), "status", "--porcelain"]).strip()
    dest.mkdir(parents=True, exist_ok=True)

    if status and not allow_dirty:
        raise BuildError(
            f"{name} has uncommitted changes, so no commit describes what would ship. Commit\n"
            f"them, or pass --allow-dirty to build from the working tree and have the manifest\n"
            f"say so.\n\n{status}"
        )

    if status:
        # Still routed through git, so ignored files stay out: this is the tracked set with local
        # modifications, not a blind copy of a directory.
        for rel in run(["git", "-C", str(repo), "ls-files"]).splitlines():
            src, dst = repo / rel, dest / rel
            if src.is_file():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
    else:
        archive = dest.parent / f"{name}.tar"
        with archive.open("wb") as fh:
            proc = subprocess.run(["git", "-C", str(repo), "archive", "HEAD"],
                                  stdout=fh, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            raise BuildError(f"{name}: git archive failed\n{proc.stderr.decode()}")
        with tarfile.open(archive) as tf:
            tf.extractall(dest, filter="data")
        archive.unlink()

    return Source(name=name, path=dest, commit=commit, dirty=bool(status))


def keep_lists(siarbuild_tree: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Read the sidecar file lists out of siar-build's own source of truth.

    ``siarbuild.vendor`` already names both sets, because it is the module that copies them into a
    generated model package: :data:`~siarbuild.vendor.VENDORED` is the eleven brahma modules the
    scanner closure needs, and :data:`~siarbuild.vendor.RUNTIME` is siar-build's own two. Parsing
    them here rather than restating them means the wheels cannot fall out of step with the code
    that reads them — a class of bug this arrangement would otherwise invite, and one that would
    surface as a model package that fails to build on a client's machine.

    Args:
        siarbuild_tree: The exported siar-build tree.

    Returns:
        ``(vendored, runtime)``.

    Raises:
        BuildError: If either assignment is missing or is no longer a literal.
    """
    path = siarbuild_tree / "src" / "siarbuild" / "vendor.py"
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise BuildError(f"cannot read {path}: {exc}") from exc

    found: dict[str, tuple[str, ...]] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in ("VENDORED", "RUNTIME"):
                try:
                    found[target.id] = tuple(ast.literal_eval(node.value))
                except ValueError as exc:
                    raise BuildError(f"{target.id} in vendor.py is not a literal: {exc}") from exc

    missing = {"VENDORED", "RUNTIME"} - set(found)
    if missing:
        raise BuildError(
            f"siarbuild/vendor.py no longer defines {', '.join(sorted(missing))} as a literal. "
            f"Rather than guess which files a model package needs, this build stops."
        )
    return found["VENDORED"], found["RUNTIME"]


# -- compilation ------------------------------------------------------------------------------


def compile_package(tree: Path, package: str, out: Path, nofollow: tuple[str, ...]) -> Path:
    """Compile one package to a single extension module.

    The only function that knows which engine is in use, so a change of mind is a local change.

    Args:
        tree: The exported source tree, holding ``src/<package>``.
        package: The importable package name.
        out: Output directory.
        nofollow: Third-party packages Nuitka must not pull in. Without these it would try to
            compile numpy and scipy along with ours, which is neither wanted nor survivable.

    Returns:
        The ``.so`` that was produced.

    Raises:
        BuildError: If Nuitka fails, or produces no extension module.
    """
    out.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "nuitka", "--module", str(tree / "src" / package),
           f"--include-package={package}", *NUITKA_FLAGS,
           *[f"--nofollow-import-to={n}" for n in nofollow],
           f"--output-dir={out}"]
    run(cmd, cwd=tree)

    built = sorted(out.glob(f"{package}.*.so")) + sorted(out.glob(f"{package}.*.pyd"))
    if not built:
        raise BuildError(f"nuitka produced no extension module for {package} in {out}")
    return built[0]


# -- wheels -----------------------------------------------------------------------------------


def build_wheel(tree: Path) -> Path:
    """Build one wheel from a source tree, without build isolation.

    Built **in isolation**, which is a network dependency accepted on purpose. Both packages
    declare ``requires = ["setuptools>=77"]`` because PEP 639's ``license`` string is not
    understood by older releases, and that is the same environment a client's
    ``pip install`` constructs. Building against whatever setuptools happens to be in the release
    machine's environment would test a configuration nobody installs — and does not work here,
    where it is 70.2.0 and rejects both files.

    The wheel this produces is a *source* wheel and is not what ships. It is built for its
    metadata — name, version, requirements, entry points, and the long description read out of
    README.md — which is fiddly to write by hand and easy to get subtly wrong.
    :func:`recompose` then replaces its payload.

    Args:
        tree: A directory holding ``pyproject.toml``.

    Returns:
        The wheel produced.

    Raises:
        BuildError: If the build produces anything other than exactly one wheel.
    """
    outdir = tree / "_wheel"
    # Run from the tree's *parent*, naming the tree as an argument. `python -m build` with the
    # tree as the working directory puts it first on sys.path, and siar-build ships a `build.py`
    # at its root -- the one a client edits three values in and runs. `-m build` imports that
    # instead of the packaging tool and evolves a model against whatever corpus it names.
    run([sys.executable, "-m", "build", "--wheel", "--outdir", str(outdir), str(tree)],
        cwd=tree.parent)
    wheels = sorted(outdir.glob("*.whl"))
    if len(wheels) != 1:
        raise BuildError(f"expected one wheel in {outdir}, found {[w.name for w in wheels]}")
    return wheels[0]


def recompose(wheel: Path, package: str, extension: Path, keep: tuple[str, ...],
              plat: str) -> Path:
    """Replace a source wheel's payload with the compiled module and its sidecar.

    Three edits to the archive, and the wheel is a different artefact afterwards:

    * every ``<package>/**.py`` is dropped, except the sidecar list;
    * the ``.so`` is added at the top level, where an extension module belongs;
    * the tags are rewritten. setuptools saw no extension in a pure-Python tree and stamped
      ``py3-none-any``, which is a lie that installs happily on 3.12 and dies at import against a
      CPython ABI it was not built for.

    ``RECORD`` is rebuilt rather than patched, because pip verifies every hash in it on install.

    Args:
        wheel: The source wheel. Left alone; a new file is written beside it.
        package: The importable package name.
        extension: The compiled module to insert.
        keep: Archive-relative glob patterns under ``<package>/`` to keep as readable data.
        plat: The wheel platform tag.

    Returns:
        The recomposed wheel.

    Raises:
        BuildError: If the wheel has no ``WHEEL``/``RECORD`` metadata.
    """
    name, version, _rest = wheel.name.split("-", 2)
    tag = f"{PYTHON_TAG}-{PYTHON_TAG}-{plat}"
    out = wheel.parent / f"{name}-{version}-{tag}.whl"

    with zipfile.ZipFile(wheel) as zin:
        items = {i.filename: zin.read(i.filename) for i in zin.infolist()}

    kept = {f"{package}/{pattern}" for pattern in keep}
    for path in list(items):
        if not path.startswith(f"{package}/"):
            continue
        if path.endswith(".py") and not any(fnmatch.fnmatch(path, k) for k in kept):
            del items[path]
        elif not path.endswith(".py") and not any(fnmatch.fnmatch(path, k) for k in kept):
            del items[path]

    items[extension.name] = extension.read_bytes()

    meta = next((n for n in items if n.endswith(".dist-info/WHEEL")), None)
    record = next((n for n in items if n.endswith(".dist-info/RECORD")), None)
    if not meta or not record:
        raise BuildError(f"{wheel.name} has no WHEEL/RECORD metadata")

    text = items[meta].decode()
    text = re.sub(r"^Tag: .*$", f"Tag: {tag}", text, flags=re.M)
    text = re.sub(r"^Root-Is-Purelib: .*$", "Root-Is-Purelib: false", text, flags=re.M)
    items[meta] = text.encode()

    lines = []
    for path, data in items.items():
        if path == record:
            continue
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        lines.append(f"{path},sha256={digest},{len(data)}")
    lines.append(f"{record},,")
    items[record] = ("\n".join(lines) + "\n").encode()

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for path, data in sorted(items.items()):
            zout.writestr(path, data)
    return out


# -- the gate ---------------------------------------------------------------------------------


def leak_check(wheel: Path, package: str, allowed: tuple[str, ...]) -> list[str]:
    """Fail a wheel that contains source it was not supposed to.

    The gate the whole exercise reduces to. It runs on the artefact rather than the tree it was
    built from, because the artefact is what a client receives.

    Two things are refused: a ``.py`` that is not on the sidecar list, and the ``.c``/``.cpp``
    that Nuitka leaves in its build directory and that a mistaken ``--remove-output`` would let
    through. A ``.py`` that is empty once comments and blank lines are stripped is not a leak.

    Args:
        wheel: The wheel to inspect.
        package: The importable package name.
        allowed: Sidecar patterns, relative to the package directory.

    Returns:
        Offending archive paths, empty when the wheel is clean.
    """
    permitted = {f"{package}/{pattern}" for pattern in allowed}
    leaks: list[str] = []
    with zipfile.ZipFile(wheel) as zf:
        for info in zf.infolist():
            path = info.filename
            if path.endswith((".c", ".cpp", ".pyx")):
                leaks.append(path)
                continue
            if not path.endswith(".py"):
                continue
            if any(fnmatch.fnmatch(path, p) for p in permitted):
                continue
            text = zf.read(path).decode("utf-8", "replace")
            body = "\n".join(line for line in text.splitlines()
                             if line.strip() and not line.lstrip().startswith("#")).strip()
            if body:
                leaks.append(path)
    return leaks


# -- pyproject surgery ------------------------------------------------------------------------


def patch_brahma_pyproject(tree: Path) -> None:
    """Pin brahma's wheel to this interpreter.

    The source library genuinely runs on 3.10; the compiled wheel genuinely does not, and metadata
    claiming otherwise turns a clean resolver error into an import-time crash on a machine nobody
    is watching.

    Args:
        tree: The exported brahma tree, modified in place.
    """
    path = tree / "pyproject.toml"
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"^requires-python = .*$",
                  f'requires-python = ">=3.13,<3.14"  # compiled against the {PYTHON_TAG} ABI',
                  text, flags=re.M)
    path.write_text(text, encoding="utf-8")


def patch_siarbuild_pyproject(tree: Path, wheels: dict[str, str], base_url: str) -> None:
    """Replace siar-build's git dependency on brahma with per-platform wheel URLs.

    Args:
        tree: The exported siar-build tree, modified in place.
        wheels: ``{platform key: wheel filename}`` for every platform built this run.
        base_url: Where those filenames are served from.

    Raises:
        BuildError: If the dependency line is absent, which means siar-build's pyproject has been
            restructured and this substitution would quietly ship a wheel that still depends on
            the private repository.
    """
    path = tree / "pyproject.toml"
    text = path.read_text(encoding="utf-8")
    pattern = r'^\s*"brahma-intelligence @ [^"]*",\n'
    if not re.search(pattern, text, flags=re.M):
        raise BuildError(
            "siar-build's pyproject has no `brahma-intelligence @ ...` line to replace. Rather "
            "than ship a wheel that still points at the private repository, this build stops."
        )

    lines = "".join(
        f'    "brahma-intelligence @ {base_url}/{wheels[key]} ; {TARGETS[key].marker}",\n'
        for key in sorted(wheels)
    )
    replacement = (
        "    # Compiled from a private source repository by siar-dist/tools/build_release.py and\n"
        "    # served as native wheels. One URL per platform, guarded by mutually exclusive\n"
        "    # markers: a direct reference cannot select a wheel by tag the way an index would,\n"
        "    # and an index cannot be named from this file in a way pip would read.\n"
        + lines
    )
    path.write_text(re.sub(pattern, replacement, text, count=1, flags=re.M), encoding="utf-8")


# -- verification -----------------------------------------------------------------------------


def external_requirements(wheels: list[Path], run_extra: bool = False) -> set[str]:
    """The third-party requirements of a set of wheels, as pip arguments.

    Read from ``METADATA`` rather than restated, so a dependency added to either package is
    installed by the next verification without anybody remembering to come here.

    Our own two are excluded: they are named by direct URL, and those URLs point at files that do
    not exist until this build's output is pushed. A verification that tried to resolve them would
    fail on every release and succeed only on the second attempt.

    Args:
        wheels: The wheels to read.
        run_extra: Also take the ``run`` extra, which is what pulls in siar-app.

    Returns:
        Requirement strings, without markers.
    """
    out: set[str] = set()
    for wheel in wheels:
        with zipfile.ZipFile(wheel) as zf:
            name = next(n for n in zf.namelist() if n.endswith(".dist-info/METADATA"))
            for line in zf.read(name).decode().splitlines():
                if not line.startswith("Requires-Dist:"):
                    continue
                req, _, marker = line.split(":", 1)[1].strip().partition(";")
                req, marker = req.strip(), marker.strip()
                if "extra ==" in marker and not (run_extra and 'extra == "run"' in marker):
                    continue
                # A direct URL is one of ours, with one exception: siar-app is public and its
                # repository resolves, and the two tests that drive its loader are the closest
                # this build gets to an end-to-end check. brahma's URL points into this build's
                # own output, which does not exist until these files are pushed, so resolving it
                # would fail on every release and succeed only on the second attempt.
                if " @ " in req and not req.lower().startswith("siar-app"):
                    continue
                out.add(req)
    return out


def verify(wheels: list[Path], workdir: Path, tests: Path | None) -> str:
    """Install the finished wheels in a throwaway environment and exercise them.

    Answers the question the leak check cannot: whether what is left after compilation still runs.

    The environment is built from nothing. An earlier version inherited system site packages to
    save fetching numpy, which is exactly the shortcut that makes such a check worthless: the
    release machine has both libraries installed from source, one of them editable, and a
    verification that can reach them is not testing the wheels. So third-party requirements are
    read out of the wheels' own metadata and installed from PyPI, and ours go in with
    ``--no-deps`` — the URL dependency between them cannot resolve until these files are pushed,
    and resolving it is not what is being checked.

    Args:
        wheels: The wheels to install.
        workdir: Where to put the environment.
        tests: A test suite to run against the installed wheels, or ``None`` to only import.

    Returns:
        A one-line summary of what was checked.

    Raises:
        BuildError: If installation, import or the suite fails.
    """
    venv = workdir / "verify-venv"
    run([sys.executable, "-m", "venv", str(venv)])
    py = venv / "bin" / "python"

    third_party = sorted(external_requirements(wheels, run_extra=tests is not None)
                         | ({"pytest"} if tests else set()))
    run([str(py), "-m", "pip", "install", "--quiet", *third_party])
    run([str(py), "-m", "pip", "install", "--no-deps", "--quiet", *[str(w) for w in wheels]])

    # Import what siar-build imports at module scope, and read the README back out of the wheel's
    # own metadata -- which is the only place it can come from once there is no source tree, and
    # therefore the thing most likely to have been lost in recomposition.
    code = (
        "import brahma_intelligence as b, siarbuild;"
        "from brahma_intelligence import BrahmaModel, ClassificationReport, apply_model,"
        " evolve_metric;"
        "from brahma_intelligence.store import Store;"
        "from siarbuild.docs import readme_markdown;"
        "from siarbuild.vendor import VENDORED, RUNTIME;"
        "n = len(readme_markdown());"
        "print(f'brahma {b.__version__}, readme {n} chars')"
    )
    summary = run([str(py), "-c", code]).strip()
    # The console script, because it is what a client types and it is the one entry
    # point that has to survive compilation -- `python -m siarbuild` no longer can.
    run([str(venv / "bin" / "siar-build"), "--help"])

    if tests is not None:
        # Selected by name with `-k`, not by node id with `--deselect`. A `--deselect` whose path
        # does not match how pytest spells the node is accepted and does nothing: the run is
        # green-looking and the excused test ran anyway, or -- as here -- it failed anyway while
        # the build claimed to have excused it. `-k` also reports "N deselected" in the summary,
        # so the exclusion appears in the same line as the result rather than only in this log.
        names = [node.split("::")[-1] for node, _ in UNRUNNABLE_COMPILED]
        for node, why in UNRUNNABLE_COMPILED:
            print(f"  not run against the wheel: {node}\n    {why}")
        expr = " and ".join(f"not {n}" for n in names)
        out = run([str(py), "-m", "pytest", str(tests), "-q", "-p", "no:cacheprovider",
                   "-k", expr], cwd=workdir)
        summary += "; " + out.strip().splitlines()[-1]
    return summary


# -- the build --------------------------------------------------------------------------------


@dataclass(slots=True)
class Release:
    """What a run produced.

    Attributes:
        wheels: Filenames placed in ``dist/``.
        sources: The exported sources and their commits.
        verified: What verification reported, or ``""`` if it was skipped.
    """

    wheels: list[str] = field(default_factory=list)
    sources: list[Source] = field(default_factory=list)
    verified: str = ""


def host_key() -> str:
    """The :data:`TARGETS` key matching this machine, or ``""`` if it is not a shipping platform."""
    system = _platform.system().lower()
    system = system if system in ("darwin", "windows") else "linux"
    machine = _platform.machine().lower()
    machine = {"amd64": "x86_64", "aarch64": "arm64"}.get(machine, machine)
    key = f"{system}-{machine}"
    return key if key in TARGETS else ""


def main(argv: list[str] | None = None) -> int:
    """Build the release. See the module docstring."""
    ap = argparse.ArgumentParser(description="Build the siar-dist download.")
    ap.add_argument("--siar-build", type=Path, default=DEFAULT_SIARBUILD)
    ap.add_argument("--brahma", type=Path, default=DEFAULT_BRAHMA)
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL,
                    help="where dist/ is served from; baked into siar-build's metadata")
    ap.add_argument("--allow-dirty", action="store_true",
                    help="build from working trees instead of HEAD, and say so in the manifest")
    ap.add_argument("--no-verify", action="store_true", help="skip the install-and-import check")
    ap.add_argument("--run-tests", action="store_true",
                    help="also run siar-build's suite against the installed wheels (slow)")
    ap.add_argument("--keep-work", action="store_true", help="leave the build directory behind")
    args = ap.parse_args(argv)

    if sys.version_info[:2] != (3, 13):
        print(f"error: this must run under CPython 3.13 — the extension is compiled against the\n"
              f"interpreter that builds it, and this is {sys.version.split()[0]}.", file=sys.stderr)
        return 2

    key = host_key()
    if not key:
        print(f"error: {_platform.system()}/{_platform.machine()} is not a shipping platform.",
              file=sys.stderr)
        return 2

    work = Path(tempfile.mkdtemp(prefix="siar-release-"))
    release = Release()
    try:
        print(f"work: {work}\nplatform: {key} ({TARGETS[key].wheel})\n")

        brahma = export(args.brahma, work / "brahma", "brahma_lib_py", args.allow_dirty)
        siarbuild = export(args.siar_build, work / "siar-build", "siar-build", args.allow_dirty)
        release.sources = [brahma, siarbuild]
        for src in release.sources:
            print(f"  {src.name:<14} {src.commit[:12]}{'  (DIRTY)' if src.dirty else ''}")

        vendored, runtime = keep_lists(siarbuild.path)
        print(f"\nsidecars, per siarbuild.vendor: {len(vendored)} brahma modules, "
              f"{len(runtime)} of our own")

        DIST.mkdir(exist_ok=True)
        target = TARGETS[key]

        print("\ncompiling brahma_intelligence")
        b_so = compile_package(brahma.path, "brahma_intelligence", work / "obj-brahma",
                               ("numpy", "scipy", "soundfile"))
        patch_brahma_pyproject(brahma.path)
        b_wheel = recompose(build_wheel(brahma.path), "brahma_intelligence", b_so,
                            vendored, target.wheel)
        leaks = leak_check(b_wheel, "brahma_intelligence", vendored)
        if leaks:
            raise BuildError(f"{b_wheel.name} carries source it should not:\n  "
                             + "\n  ".join(leaks[:20]))
        shutil.copy2(b_wheel, DIST / b_wheel.name)
        release.wheels.append(b_wheel.name)
        print(f"  {b_wheel.name}  leak check clean")

        print("\ncompiling siarbuild")
        s_so = compile_package(siarbuild.path, "siarbuild", work / "obj-siarbuild",
                               ("numpy", "soundfile", "brahma_intelligence"))
        patch_siarbuild_pyproject(siarbuild.path, {key: b_wheel.name}, args.base_url)
        s_keep = (*runtime, "template/*.tmpl")
        s_wheel = recompose(build_wheel(siarbuild.path), "siarbuild", s_so, s_keep, target.wheel)
        leaks = leak_check(s_wheel, "siarbuild", s_keep)
        if leaks:
            raise BuildError(f"{s_wheel.name} carries source it should not:\n  "
                             + "\n  ".join(leaks[:20]))
        shutil.copy2(s_wheel, DIST / s_wheel.name)
        release.wheels.append(s_wheel.name)
        print(f"  {s_wheel.name}  leak check clean")

        if not args.no_verify:
            print("\nverifying")
            tests = siarbuild.path / "tests" if args.run_tests else None
            release.verified = verify([DIST / n for n in release.wheels], work, tests)
            print(f"  {release.verified}")

        manifest = {
            "python_tag": PYTHON_TAG,
            "platform": key,
            "engine": "nuitka",
            "verified": release.verified,
            "base_url": args.base_url,
            "sources": {s.name: {"commit": s.commit, "dirty": s.dirty}
                        for s in release.sources},
            "wheels": {n: hashlib.sha256((DIST / n).read_bytes()).hexdigest()
                       for n in release.wheels},
        }
        (DIST / "RELEASE.json").write_text(json.dumps(manifest, indent=2) + "\n",
                                           encoding="utf-8")

        print("\ndist/")
        for n in release.wheels:
            print(f"  {n}  ({(DIST / n).stat().st_size // 1024} KiB)")
        print("  RELEASE.json")
        print(f"\nInstall:\n  pip install {args.base_url}/{s_wheel.name}")
        if any(s.dirty for s in release.sources):
            print("\nNOTE: built from a dirty tree. RELEASE.json records it. Do not ship it.")
        return 0

    except BuildError as exc:
        print(f"\nerror: {exc}", file=sys.stderr)
        return 1
    finally:
        if args.keep_work:
            print(f"\nwork kept at {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
