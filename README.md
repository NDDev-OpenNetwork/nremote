# nremote

Remote desktop that connects through a rendezvous server **you** run, not a
vendor's cloud.

The server is [nremote-server](https://github.com/NDDev-OpenNetwork/nremote-server).
This repository is the client: desktop and mobile, Rust and Flutter.

## What is different about this client

- **It makes no outbound call of its own.** No update check, no usage report, no
  device fingerprint, and no default API server. The upstream client asked a
  third-party endpoint for the latest version once a day and every start, and
  the request carried the host's distribution, OS version, architecture and a
  fingerprint derived from the machine. That is gone, along with the module that
  computed the fingerprint and the auto-updater the request fed.
- **It has no compiled-in server.** A build with no configuration reaches
  nothing, deliberately. The address and public key are supplied at build time.
- **It trusts nobody's signing key but its own operator's.** The upstream client
  accepted a `custom.txt` configuration blob signed by the vendor's key. That
  key is removed.

The rendezvous protocol is unchanged, so this client works with an upstream
server and `nremote-server` works with an upstream client. Migration can be
incremental.

## Pointing a client at a server

Two values, neither of them secret — every client that connects has to know
both:

- **ID Server**: the host running `hbbs`, for example `remote.example.com`
- **Key**: the contents of the server's `id_ed25519.pub`

Set them in the client under Settings → Network, or compile them in:

```bash
NREMOTE_RENDEZVOUS=remote.example.com \
NREMOTE_KEY=BASE64_PUBLIC_KEY \
python3 scripts/configure.py
```

`configure.py` validates both: the key must decode to 32 bytes, the host must be
a host rather than a URL, and supplying one without the other is refused. A
client that knows where to connect but cannot authenticate what it reaches is
not a state worth shipping.

Leave Relay Server and API Server blank. The relay is derived from the ID
server, and there is no API server in this build.

## Privacy

This client sends nothing anywhere except to the rendezvous server and the peer
you connect to. There is no telemetry, no analytics, no crash reporting and no
update check. Connections are end-to-end encrypted between peers; the
rendezvous server brokers them and the relay, when one is needed, carries
ciphertext it cannot read.

What the server operator can see is what a rendezvous server must see: which IDs
are online, and which pairs asked to be introduced. If you run the server, that
is you.

## Building

```bash
python3 scripts/brand.py --check            # the identity has not reverted
python3 scripts/check_protocol_parity.py    # the wire protocol matches the server
cargo build --locked --manifest-path libs/hbb_common/Cargo.toml
```

The full application build needs a Flutter SDK, vcpkg and a long list of system
libraries; see `.github/workflows/`. The shared library builds on its own and is
what CI checks on every pull request.

### x11-required

The Linux client captures the screen through X11. On a Wayland session it uses
the portal where one is available and falls back to X11 otherwise; a session
with neither cannot be captured. If the client reports that X11 is required, log
into an X11 session or install the desktop portal for your compositor.

### login-screen

Connecting to a machine that is sitting at its login screen needs the client
installed as a system service, because a user session does not exist yet. An
unattended install is what makes the login screen reachable; a portable run
cannot see it.

### headless-linux

A Linux machine with no physical display can still be controlled, but something
has to provide a display for it. Run a virtual X server and point the session at
it. Without one there is no framebuffer to capture and the client will connect
and show nothing.

## Licence

AGPL-3.0-or-later. See [LICENCE](LICENCE), and [NOTICE](NOTICE) for the
attribution and the list of modifications this repository carries.
