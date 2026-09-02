#!/usr/bin/env python3
"""Rename the product identity in this tree, and prove it stays renamed.

This repository is derived from a prior work whose name appears about four
thousand times across Rust, Dart, Kotlin, Swift, C++, XML, plists and Xcode
project files. Renaming that by hand once would be an afternoon; renaming it
again after every upstream merge would be how the name comes back. So it is a
tool, and `--check` is a gate.

What it must not touch, and why:

  * Dependency source URLs. Twenty git dependencies in the two Cargo manifests
    resolve from `github.com/rustdesk-org/...` and `github.com/rustdesk/...`.
    Those are addresses, not branding: rewriting one produces a manifest that
    cannot resolve. They are masked before the rename and restored after.
  * `Cargo.lock`, which is generated and carries the same URLs.
  * `LICENCE` and `NOTICE`, where the prior work is named because the licence
    requires it.

Server address and key are NOT set here. They are build inputs, and a public
repository does not carry the address of a private deployment; see
`scripts/configure.py`.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

# The three cases the source actually uses, longest first so that a shorter
# pattern cannot eat the prefix of a longer one.
RENAMES = (
    ("RUSTDESK", "NREMOTE"),
    ("RustDesk", "NRemote"),
    ("rustdesk", "nremote"),
)

# Anything matching these is an address. Masked before the rename.
PROTECTED = (
    re.compile(r"https?://[^\s\"'<>)\]]*rustdesk[^\s\"'<>)\]]*", re.IGNORECASE),
    re.compile(r"\bgithub\.com/rustdesk[\w./-]*", re.IGNORECASE),
)

SKIP_FILES = {"Cargo.lock", "LICENCE", "LICENSE", "NOTICE", "scripts/brand.py"}
SKIP_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".ico", ".icns", ".gif", ".webp", ".woff", ".woff2",
    ".ttf", ".otf", ".zip", ".gz", ".xz", ".so", ".dll", ".dylib", ".a", ".bin",
    ".sqlite3", ".pdb", ".jar", ".keystore", ".jks",
}

# Paths whose *name* carries the identity.
PATH_RENAMES = {
    "flatpak/com.rustdesk.RustDesk.metainfo.xml": "flatpak/com.nddev.NRemote.metainfo.xml",
    "flatpak/rustdesk.json": "flatpak/nremote.json",
    "flutter/lib/models/rustdesk_terminal.dart": "flutter/lib/models/nremote_terminal.dart",
    "res/msi/Package/Components/RustDesk.wxs": "res/msi/Package/Components/NRemote.wxs",
    "res/rustdesk-banner.svg": "res/nremote-banner.svg",
    "res/rustdesk-link.desktop": "res/nremote-link.desktop",
    "res/rustdesk.desktop": "res/nremote.desktop",
    "res/rustdesk.service": "res/nremote.service",
}


def tracked_files() -> list[pathlib.Path]:
    raw = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "-z"])
    return [ROOT / item.decode() for item in raw.split(b"\0") if item]


def skipped(path: pathlib.Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    return (
        rel in SKIP_FILES
        or path.name in SKIP_FILES
        or path.suffix.lower() in SKIP_SUFFIXES
    )


def rename_text(text: str) -> str:
    """Apply the renames with every address masked out of the way."""
    masked: list[str] = []

    def hide(match: re.Match[str]) -> str:
        masked.append(match.group(0))
        return f"\x00{len(masked) - 1}\x00"

    for pattern in PROTECTED:
        text = pattern.sub(hide, text)
    for old, new in RENAMES:
        text = text.replace(old, new)
    for index, original in enumerate(masked):
        text = text.replace(f"\x00{index}\x00", original)
    return text


def findings(text: str) -> int:
    """Occurrences that survive masking -- that is, real branding."""
    stripped = text
    for pattern in PROTECTED:
        stripped = pattern.sub("", stripped)
    return sum(stripped.count(old) for old, _ in RENAMES)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report what is unbranded and exit non-zero; change nothing",
    )
    args = parser.parse_args()

    remaining: dict[str, int] = {}
    changed: list[str] = []

    for path in tracked_files():
        if skipped(path) or not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, IsADirectoryError):
            continue
        rel = path.relative_to(ROOT).as_posix()
        if args.check:
            count = findings(text)
            if count:
                remaining[rel] = count
            continue
        renamed = rename_text(text)
        if renamed != text:
            path.write_text(renamed, encoding="utf-8")
            changed.append(rel)

    for old, new in PATH_RENAMES.items():
        source, target = ROOT / old, ROOT / new
        if args.check:
            if source.exists():
                remaining[old] = remaining.get(old, 0) + 1
            continue
        if source.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            subprocess.check_call(["git", "-C", str(ROOT), "mv", old, new])
            changed.append(f"{old} -> {new}")

    if args.check:
        if remaining:
            print("unbranded, and this is a gate rather than a report:", file=sys.stderr)
            for rel, count in sorted(remaining.items(), key=lambda item: -item[1]):
                print(f"  {count:5}  {rel}", file=sys.stderr)
            print(
                f"\n{sum(remaining.values())} occurrences in {len(remaining)} files."
                "\nRun scripts/brand.py to fix, then review the diff.",
                file=sys.stderr,
            )
            return 1
        print("branded: no unprotected occurrence of the prior name remains")
        return 0

    print(f"rewrote {len(changed)} paths")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
