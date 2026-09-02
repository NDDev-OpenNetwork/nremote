#!/usr/bin/env python3
"""Compile the server address and public key into the client.

Both values live in `libs/hbb_common/src/config.rs` as constants, because that
is where the program reads them; there is no `option_env!` to hook and adding
one would mean a client whose server can be changed by an environment variable
at run time, which is not what "compiled in" should mean.

They are **not** committed. This repository is public and a deployment's
address is a fact about a private estate, so the defaults are empty and the
real values arrive at build time:

    NREMOTE_RENDEZVOUS=remote.example.com \\
    NREMOTE_KEY=BASE64_PUBLIC_KEY \\
    python3 scripts/configure.py

Neither value is secret -- every client that connects has to know both -- but
"not secret" and "belongs in a public repository" are different questions, and
this is the second one.

`--check` prints what is currently compiled in without changing anything.
"""

from __future__ import annotations

import argparse
import base64
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / "libs/hbb_common/src/config.rs"

SERVERS = re.compile(r"^pub const RENDEZVOUS_SERVERS: &\[&str\] = (.+);$", re.M)
PUB_KEY = re.compile(r'^pub const RS_PUB_KEY: &str = "(.*)";$', re.M)

# A hostname or an IPv4 literal, optionally with a port. Deliberately strict:
# a typo here produces a client that cannot reach anything, and the failure
# surfaces on somebody's laptop rather than in this run.
HOST = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?(:\d{1,5})?$")


def validate_key(value: str) -> str:
    """An ed25519 public key, base64, 32 bytes. Anything else is a typo."""
    try:
        raw = base64.b64decode(value, validate=True)
    except Exception as error:  # noqa: BLE001 - the message is the point
        raise SystemExit(f"NREMOTE_KEY is not valid base64: {error}")
    if len(raw) != 32:
        raise SystemExit(
            f"NREMOTE_KEY decodes to {len(raw)} bytes; an ed25519 public key is 32. "
            "This is the contents of the server's id_ed25519.pub."
        )
    return value


def validate_host(value: str) -> str:
    if not HOST.match(value):
        raise SystemExit(
            f"NREMOTE_RENDEZVOUS is not a host or host:port: {value!r}. "
            "No scheme, no path -- the client dials it, it does not fetch it."
        )
    return value


def read_current(text: str) -> tuple[str, str]:
    servers = SERVERS.search(text)
    key = PUB_KEY.search(text)
    if not servers or not key:
        raise SystemExit(f"cannot find the constants in {CONFIG}; has the file moved?")
    return servers.group(1), key.group(1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="print, change nothing")
    args = parser.parse_args()

    text = CONFIG.read_text(encoding="utf-8")
    servers, key = read_current(text)

    if args.check:
        print(f"RENDEZVOUS_SERVERS = {servers}")
        print(f"RS_PUB_KEY         = {key or '(empty)'}")
        return 0

    host = os.environ.get("NREMOTE_RENDEZVOUS", "").strip()
    pub = os.environ.get("NREMOTE_KEY", "").strip()
    if not host or not pub:
        raise SystemExit(
            "NREMOTE_RENDEZVOUS and NREMOTE_KEY must both be set.\n"
            "Setting one without the other produces a client that knows where to "
            "connect and cannot authenticate what it reaches, or the reverse. "
            "Neither is a state worth shipping."
        )
    host = validate_host(host)
    pub = validate_key(pub)

    text = SERVERS.sub(
        lambda _: f'pub const RENDEZVOUS_SERVERS: &[&str] = &["{host}"];', text, count=1
    )
    text = PUB_KEY.sub(
        lambda _: f'pub const RS_PUB_KEY: &str = "{pub}";', text, count=1
    )
    CONFIG.write_text(text, encoding="utf-8")

    servers, key = read_current(CONFIG.read_text(encoding="utf-8"))
    print(f"configured RENDEZVOUS_SERVERS = {servers}")
    print(f"configured RS_PUB_KEY         = {key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
