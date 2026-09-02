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

# One case-insensitive pattern, with the replacement derived from the shape of
# what it matched. The first version listed three literal spellings, and that
# is exactly how it missed two: `Rustdesk` in the Dart FFI binding and
# `rustDesk` in 45 identifiers. Worse, `--check` counted the same three
# literals, so the gate was blind to precisely what it existed to catch and
# reported the tree clean. A list of spellings is a guess about what the source
# contains; a pattern is not.
TOKEN = re.compile(r"rustdesk", re.IGNORECASE)


def _rename_token(match: "re.Match[str]") -> str:
    text = match.group(0)
    if text.isupper():
        return "NREMOTE"
    if text.islower():
        return "nremote"
    if text[0].isupper():
        return "NRemote"  # RustDesk, Rustdesk
    return "nRemote"  # rustDesk, and any other lowercase-initial mixed case

# Dependency source addresses. Masked before the rename, restored after.
#
# Only `github.com/rustdesk...`, and the narrowness is deliberate: an earlier
# version protected every URL containing the name, which preserved the "Website",
# "Download" and "Privacy Statement" links in the user interface -- branding
# wearing a URL's clothes. Those are rewritten by the table below instead.
PROTECTED = (
    re.compile(r"\bgithub\.com/rustdesk[\w./-]*", re.IGNORECASE),
    # Git refs on a dependency line. `portable-pty` resolves from a branch
    # literally called `rustdesk/pty_based_0.8.1`, and the first version of
    # this tool renamed the branch while carefully preserving the URL beside
    # it -- producing a manifest that pointed at a branch which does not
    # exist. A ref is an address too.
    re.compile(r'\b(?:branch|tag|rev)\s*=\s*"[^"]*"'),
)

# Product links that point at the prior work's website. A mechanical rename
# would turn these into `nremote.com`, a domain we do not own and somebody else
# might, which is worse than leaving them. Each one is redirected to the place
# that actually answers the same question here, and the anchors are a promise
# the README keeps.
HOME = "https://github.com/NDDev-OpenNetwork/nremote"
URL_REWRITES = {
    "https://rustdesk.com/docs/en/manual/linux/#x11-required": f"{HOME}#x11-required",
    "https://rustdesk.com/docs/en/manual/linux/#login-screen": f"{HOME}#login-screen",
    "https://rustdesk.com/docs/en/": HOME,
    "https://rustdesk.com/blog/id-relay-set/": f"{HOME}#pointing-a-client-at-a-server",
    "https://rustdesk.com/download": f"{HOME}/releases",
    "https://rustdesk.com/privacy.html": f"{HOME}#privacy",
    "http://rustdesk.com/privacy": f"{HOME}#privacy",
    "https://rustdesk.com/": HOME,
    "https://rustdesk.com": HOME,
}

# Files whose job is to explain the derivation have to be allowed to name it.
# NOTICE because the licence requires it; .gitleaks.toml because an allowlist
SKIP_FILES = {
    "Cargo.lock",
    "LICENCE",
    "LICENSE",
    "NOTICE",
    ".gitleaks.toml",  # entry that cannot say what it allows is not reviewable
    "scripts/brand.py",
}
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


# The prior work's public server key, which appears 81 times across 42
# translation files inside a help tip that shows an example connection string.
# A base64 blob has no name in it, so nothing else here would touch it -- and a
# third party's real key in our user interface is neither documentation nor
# ours.
#
# The replacement is a placeholder rather than a realistic-looking key, and that
# is the second attempt. The first was base64 that decoded to "nremote example
# key -- not real!", which is self-documenting to a human and indistinguishable
# from a credential to a secret scanner: it produced 79 findings, all of them
# the thing that was supposed to fix the findings. A placeholder cannot make
# that mistake, and the same sentence already uses `<key_value>` for the
# abstract form, so it reads consistently.
LITERAL_REWRITES = {
    "5Qbwsde3unUcJBtrx9ZkvUmwFNoExHzpryHuPUdqlWM=": "<your-server-key>",
    "bnJlbW90ZSBleGFtcGxlIGtleSAtLSBub3QgcmVhbCE=": "<your-server-key>",
    # A bare hostname in a test fixture. `socket_client`'s NAT64 test resolves
    # it for real, so the mechanical rename pointed a live DNS lookup at
    # `nremote.com` -- a domain nobody here owns -- and the test failed in CI.
    # RFC 2606 reserves `example.com` for exactly this.
    "rustdesk.com": "example.com",
}


def rename_text(text: str) -> str:
    """Apply the renames with every dependency address masked out of the way."""
    # URLs first, longest first, so that `https://rustdesk.com/docs/en/` is not
    # eaten by the bare `https://rustdesk.com` entry -- and so that the bare-host
    # literal below cannot pull the host out of a URL before its own entry
    # matches.
    for old_url in sorted(URL_REWRITES, key=len, reverse=True):
        text = text.replace(old_url, URL_REWRITES[old_url])
    for old_literal, new_literal in LITERAL_REWRITES.items():
        text = text.replace(old_literal, new_literal)

    masked: list[str] = []

    def hide(match: re.Match[str]) -> str:
        masked.append(match.group(0))
        return f"\x00{len(masked) - 1}\x00"

    for pattern in PROTECTED:
        text = pattern.sub(hide, text)
    text = TOKEN.sub(_rename_token, text)
    for index, original in enumerate(masked):
        text = text.replace(f"\x00{index}\x00", original)
    return text


def findings(text: str) -> int:
    """Occurrences that survive masking -- that is, real branding."""
    stripped = text
    for pattern in PROTECTED:
        stripped = pattern.sub("", stripped)
    for replacement in URL_REWRITES.values():
        stripped = stripped.replace(replacement, "")
    return len(TOKEN.findall(stripped)) + sum(
        stripped.count(old) for old in LITERAL_REWRITES
    )


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
