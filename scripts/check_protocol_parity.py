#!/usr/bin/env python3
"""Prove the wire protocol is identical to the server's.

`nremote-server` and this client each vendor the shared library, at different
upstream commits, because each needs to change files the other does not. That
is a deliberate divergence with one thing it must never touch: the rendezvous
protocol. A field renamed on one side produces a client that connects, a server
that listens, and a device that never registers -- no error anywhere.

So the digest is pinned here and checked two ways. Locally, that this
repository's copy is the pinned one. Over the network, that the server's copy
at the pinned release is the same bytes. The second is the one that catches a
divergence introduced on the other side, which is the direction nothing else
looks.

    python3 scripts/check_protocol_parity.py            # both halves
    python3 scripts/check_protocol_parity.py --offline  # local half only
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
PIN = ROOT / "protocol-parity.json"
RAW = "https://raw.githubusercontent.com/{repo}/{ref}/{path}"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="check this repository's copy only; do not fetch the server's",
    )
    args = parser.parse_args()

    pin = json.loads(PIN.read_text(encoding="utf-8"))
    repo, ref = pin["peer_repository"], pin["peer_ref"]
    failures = 0

    for path, expected in sorted(pin["files"].items()):
        local = ROOT / path
        if not local.is_file():
            print(f"FAIL {path}: not in this repository", file=sys.stderr)
            failures += 1
            continue
        actual = digest(local.read_bytes())
        if actual != expected:
            print(
                f"FAIL {path}: this repository has {actual[:16]}…, "
                f"the pin says {expected[:16]}…",
                file=sys.stderr,
            )
            failures += 1
        else:
            print(f"ok   {path} matches the pin")

        if args.offline:
            continue

        url = RAW.format(repo=repo, ref=ref, path=path)
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                peer = digest(response.read())
        except (urllib.error.URLError, TimeoutError) as error:
            # Not a pass. A check that cannot reach its subject has not
            # answered the question, and saying so is the whole point.
            print(f"FAIL {path}: could not fetch {repo}@{ref}: {error}", file=sys.stderr)
            failures += 1
            continue
        if peer != expected:
            print(
                f"FAIL {path}: {repo}@{ref} has {peer[:16]}…, "
                f"the pin says {expected[:16]}…",
                file=sys.stderr,
            )
            failures += 1
        else:
            print(f"ok   {path} matches {repo}@{ref}")

    if failures:
        print(
            f"\n{failures} parity failure(s). Either the protocol really changed, in "
            "which case both sides move together and the pin is updated in the same "
            "breath, or one side drifted and must be put back.",
            file=sys.stderr,
        )
        return 1
    print("\nwire protocol parity holds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
