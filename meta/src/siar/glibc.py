# Vixen Intelligence c.2026
"""Turning "GLIBC_2.29 not found" into a sentence somebody can act on.

Every wheel in this download except this one is a native extension compiled by Nuitka against the
build machine's C library. A wheel is tagged ``linux_x86_64``, which pip installs on *any* x86_64
Linux — there is no glibc floor in a wheel tag, so an install that cannot possibly run succeeds
quietly and the failure arrives later, as this::

    ImportError: /lib/x86_64-linux-gnu/libm.so.6: version `GLIBC_2.29' not found
    (required by .../siardb.cpython-313-x86_64-linux-gnu.so)

Three things are wrong with that message as a thing to hand a client. It names a library rather
than a product, so it does not say which part of the download is broken. It does not say what this
machine actually has, so there is nothing to compare against. And the version it names is **not the
version needed** — the dynamic loader stops at the first requirement it cannot satisfy, and a
module that wants 2.29, 2.34 and 2.38 reports only 2.29. Upgrading to exactly what the error asked
for is the obvious response and it does not work.

So this module reads the floor off the extension itself. The ``.gnu.version_r`` section of an ELF
object lists every symbol version it needs by name; the highest ``GLIBC_x.y`` in it is the real
answer, and it is a property of the artefact that shipped rather than of a table somebody has to
remember to update when the build machine moves.

Pure standard library, and it must stay that way: this runs *because* an import already failed,
and a diagnostic that needs a dependency of its own is a second traceback on top of the first.
"""
from __future__ import annotations

import os
import re
import struct

__all__ = [
    "DISTRO_FLOORS",
    "explain",
    "installed",
    "is_glibc_error",
    "required",
]

#: ``SHT_GNU_verneed`` — the section listing the symbol versions an object needs from elsewhere.
#: Found by type rather than by name, which saves resolving the section-name string table.
_SHT_GNU_VERNEED = 0x6FFFFFFE

#: What distributions ship, so "you need 2.38" can be answered with "so upgrade to this".
#: Deliberately the oldest release at or above each floor rather than an exhaustive table: the
#: question a client is asking is "what do I have to be on", not "list every Linux".
DISTRO_FLOORS: tuple[tuple[tuple[int, int], str], ...] = (
    ((2, 17), "RHEL/CentOS 7, Ubuntu 14.04"),
    ((2, 27), "Ubuntu 18.04"),
    ((2, 28), "Debian 10, RHEL 8"),
    ((2, 31), "Ubuntu 20.04"),
    ((2, 34), "Ubuntu 22.04, Debian 12, RHEL 9, Fedora 35"),
    ((2, 38), "Ubuntu 23.10, Debian 13, Fedora 38"),
    ((2, 39), "Ubuntu 24.04"),
)

_GLIBC_VERSION = re.compile(r"GLIBC_(\d+)\.(\d+)")


def installed() -> tuple[int, int] | None:
    """This machine's glibc version, or ``None`` if it does not have one.

    Returns:
        ``(major, minor)``, or ``None`` on a system with no glibc at all — musl (Alpine) being the
        one that matters here, because it matches the same wheel tag and fails the same way.

    Note:
        ``os.confstr`` first because it asks the C library itself. ``platform.libc_ver`` is the
        obvious alternative and is not used: it works by scanning the Python executable for version
        strings, which reports the libc Python was *built* against rather than the one now loaded.
    """
    try:
        answer = os.confstr("CS_GNU_LIBC_VERSION")
    except (ValueError, OSError, AttributeError):
        answer = None
    if answer:
        found = re.search(r"(\d+)\.(\d+)", answer)
        if found:
            return int(found.group(1)), int(found.group(2))

    # A glibc too old to answer confstr, or a libc that is not glibc. Ask the library directly
    # before concluding it is absent.
    try:
        import ctypes

        libc = ctypes.CDLL("libc.so.6")
        libc.gnu_get_libc_version.restype = ctypes.c_char_p
        found = re.search(r"(\d+)\.(\d+)", libc.gnu_get_libc_version().decode("ascii", "replace"))
        if found:
            return int(found.group(1)), int(found.group(2))
    except Exception:  # noqa: BLE001 — no glibc, or one without this symbol. Both mean "unknown".
        pass
    return None


def required(path: str) -> tuple[int, int] | None:
    """The highest glibc version a compiled extension needs, read out of the file.

    Args:
        path: The ``.so`` that failed to load.

    Returns:
        ``(major, minor)``, or ``None`` if the file cannot be read or is not an ELF64 object.

    Note:
        This is the number the loader does not give you. It stops at the first version it cannot
        satisfy, so an object needing 2.29, 2.34 and 2.38 raises about 2.29 — and a client who
        upgrades to 2.29 is still broken, having done the work the error asked for.
    """
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError:
        return None

    # ELF64 little-endian only. Everything this project ships is x86_64, and a guess about any
    # other layout would be a wrong number rather than an absent one.
    if len(data) < 64 or data[:4] != b"\x7fELF" or data[4] != 2 or data[5] != 1:
        return None

    try:
        e_shoff, = struct.unpack_from("<Q", data, 0x28)
        e_shentsize, e_shnum = struct.unpack_from("<HH", data, 0x3A)

        best: tuple[int, int] | None = None
        for i in range(e_shnum):
            off = e_shoff + i * e_shentsize
            sh_type, = struct.unpack_from("<I", data, off + 4)
            if sh_type != _SHT_GNU_VERNEED:
                continue
            sh_offset, sh_size = struct.unpack_from("<QQ", data, off + 0x18)
            sh_link, = struct.unpack_from("<I", data, off + 0x28)

            # sh_link names the string table the version names live in, so the section-name table
            # never has to be resolved.
            str_off = e_shoff + sh_link * e_shentsize
            strtab, = struct.unpack_from("<Q", data, str_off + 0x18)

            for name in _verneed_names(data, sh_offset, sh_size, strtab):
                found = _GLIBC_VERSION.fullmatch(name)
                if found:
                    version = (int(found.group(1)), int(found.group(2)))
                    if best is None or version > best:
                        best = version
        return best
    except (struct.error, IndexError):
        return None


def _verneed_names(data: bytes, offset: int, size: int, strtab: int):
    """Yield every version name in a ``.gnu.version_r`` section.

    The section is a linked list of ``Verneed`` records — one per library depended on — each
    carrying its own linked list of ``Vernaux`` records, one per version wanted from it. Both
    chains are byte offsets relative to their own record, and both terminate on a zero next.
    """
    cursor = offset
    end = offset + size
    while cursor < end:
        vn_cnt, = struct.unpack_from("<H", data, cursor + 2)
        vn_aux, vn_next = struct.unpack_from("<II", data, cursor + 8)
        aux = cursor + vn_aux
        for _ in range(vn_cnt):
            if aux >= end:
                break
            vna_name, vna_next = struct.unpack_from("<II", data, aux + 8)
            yield _string_at(data, strtab + vna_name)
            if not vna_next:
                break
            aux += vna_next
        if not vn_next:
            break
        cursor += vn_next


def _string_at(data: bytes, offset: int) -> str:
    """One NUL-terminated string out of a string table."""
    end = data.find(b"\0", offset)
    return data[offset:end if end != -1 else None].decode("ascii", "replace")


def is_glibc_error(exc: BaseException) -> bool:
    """Whether this exception is the one this module exists to explain.

    Args:
        exc: The exception an import raised.

    Returns:
        True for the loader's version-not-found message. Narrow on purpose — an unrelated
        ImportError dressed up in this module's advice would send somebody after their C library
        for a problem that is not there.
    """
    return isinstance(exc, ImportError) and "GLIBC_" in str(exc) and "not found" in str(exc)


def _object_path(message: str) -> str:
    """The ``.so`` named in a loader error, or ``""``.

    The message ends ``(required by /path/to/thing.so)``, and it is the *required by* path that
    matters — the path at the front is the system library that came up short.
    """
    found = re.search(r"required by ([^\s)]+\.so[^\s)]*)", message)
    return found.group(1) if found else ""


def _upgrade_to(floor: tuple[int, int]) -> str:
    """The oldest distribution at or above ``floor``, phrased as advice."""
    for version, distros in DISTRO_FLOORS:
        if version >= floor:
            return distros
    return ""


def explain(exc: BaseException, program: str = "") -> str:
    """The whole message to print instead of a traceback.

    Args:
        exc: The ImportError the loader raised.
        program: Which command was being run, if known.

    Returns:
        A block of text ending without a newline, ready for ``print(..., file=sys.stderr)``.
    """
    message = str(exc)
    obj = _object_path(message)
    have = installed()
    need = required(obj) if obj else None

    what = f"{program} cannot start" if program else "This install cannot start"
    lines = [
        f"error: {what} — the C library on this machine is too old for it.",
        "",
    ]

    lines.append(f"  this machine has  glibc {have[0]}.{have[1]}" if have else
                 "  this machine has  no glibc (musl, e.g. Alpine — not a supported platform)")
    if need:
        lines.append(f"  this build needs  glibc {need[0]}.{need[1]} or newer")
    else:
        # The floor could not be read, so the loader's own number is all there is — and it is a
        # lower bound, which the message has to say rather than imply.
        first = _GLIBC_VERSION.search(message)
        asked = f"{first.group(1)}.{first.group(2)}" if first else "a newer version"
        lines.append(f"  this build needs  at least glibc {asked} (possibly higher; the loader")
        lines.append("                    reports only the first version it cannot satisfy)")

    if obj:
        lines += ["", f"  the module is     {obj}"]

    if need:
        upgrade = _upgrade_to(need)
        lines += ["", "What to do:", ""]
        if upgrade:
            lines.append(f"  Run it on {upgrade} or newer. glibc is the")
            lines.append("  core of a Linux distribution and is not upgraded on its own — upgrading")
            lines.append("  it means upgrading the distribution, or using a container:")
        else:
            lines.append("  Run it on a newer distribution, or in a container:")
        lines += [
            "",
            f"      docker run -it --rm -v $PWD:/work ubuntu:24.04",
            "",
            "  If neither is possible, ask Vixen Intelligence for a build against an older glibc.",
            "  Nothing about the program requires a recent one; the wheels are simply compiled on",
            "  a current machine, and a build made on an older one runs on both.",
        ]

    lines += ["", "The original error follows.", "", f"  {message}"]
    return "\n".join(lines)
