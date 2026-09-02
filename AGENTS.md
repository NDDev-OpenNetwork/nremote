# AGENTS.md — nremote

## Where the instructions live

This file, and only this file. It arrived alongside a `CLAUDE.md` containing
`@AGENTS.md` and a `GEMINI.md` containing `AGENTS.md` -- two pointers whose only
job was to make other tools read this one. Both are gone, because every other
public module in this organization carries `AGENTS.md` alone and a second
instruction path is a second thing to keep in step.

If a tool needs this file loaded and will not find it, point that tool at it.
Do not add a copy.

## What this is

The remote desktop client for [nremote-server](https://github.com/NDDev-OpenNetwork/nremote-server).
Public, AGPL-3.0, part of `NDDev-OpenNetwork`. `NOTICE` records the prior work
this is derived from and every modification since; add to that list when you
make one that belongs there.

## Three invariants, and each has a gate

**No outbound call the operator did not ask for.** No update check, no
telemetry, no fingerprint, no default API server. If a change needs to contact
a host the operator did not configure, that is a change in what the product is:
it is opt-in, logged, and written into NOTICE. Nothing currently gates this
automatically — it is a rule, and reviewing a diff for a new HTTP client is
part of reviewing a diff.

**The product identity does not revert.** `scripts/brand.py --check` runs in
CI. An upstream merge that reintroduces the prior name breaks nothing at build
time, which is exactly why it needs a gate. Re-run `scripts/brand.py` as part
of merging, then read the diff.

The tool masks dependency source addresses — twenty git dependencies resolve
from `github.com/rustdesk-org/…` — and rewrites product links through an
explicit table. Do not widen the mask to "any URL containing the name": that
was the first version, and it preserved the "Website", "Download" and "Privacy
Statement" links in the user interface, which is branding wearing a URL's
clothes.

**The wire protocol matches the server.** `scripts/check_protocol_parity.py`
pins `libs/hbb_common/protos/rendezvous.proto` by digest and checks it twice:
against this repository, and against `nremote-server` at its pinned release.
The second half is the one that catches a divergence introduced on the other
side. A protocol change moves both repositories and updates the pin in the same
breath. A field renamed on one side alone produces a client that connects, a
server that listens, and a device that never registers — with no error
anywhere.

## No server configuration in this repository

`RENDEZVOUS_SERVERS` and `RS_PUB_KEY` are empty here and CI fails if they are
not. This repository is public; a deployment's address is a fact about a
private estate. Neither value is secret — every client needs both — but "not
secret" and "belongs in a public repository" are different questions.

The build supplies them through `scripts/configure.py`, which validates that
the key is 32 bytes of base64 and the host is a host rather than a URL.

## libs/hbb_common is vendored, not a dependency

It arrived as a submodule and is now part of this tree, because branding and
the telemetry removal both need to change files inside it and a consuming
repository cannot commit into a submodule.

`nremote-server` vendors the same library at an earlier upstream commit. Two
copies is a liability with one thing it must never touch, and that thing has
the parity check above. Consolidating them into a third repository both
consume is the right end state and is declared work, not a habit.

Upstream changes to that directory are merged by hand. There is no gitlink to
bump.

## Open work, named rather than implied

- **The auto-updater module.** Its network path is dead — the request that set
  `SOFTWARE_UPDATE_URL` is gone, so the download can never start — and the two
  entry points return before it. What remains is several hundred lines of
  Windows and macOS installer code behind `#[allow(unreachable_code)]`.
  Deleting it is right and is a change that needs a macOS and Windows build to
  believe, which is why it is not folded into the commit that disabled it.
- **A shared `nremote-common`.** See above.
- **The advisory backlog in the application lockfile.** 32 open Dependabot
  alerts on 2026-09-02. Two of them are `atty`, once per lockfile, and it has
  no patched version at all — it reaches here through `bindgen` under
  `machine-uid`, so it goes when that does. There is one lockfile for the
  workspace — `libs/hbb_common` is a member, not an independent crate — so
  there was nothing smaller to scan honestly, and until `build.yml` existed
  there was no way to verify an update. Both conditions are gone:
  Dependabot opens the updates, `build.yml` compiles them on all three
  platforms and `dependency-review` refuses anything new. `security.yml` still
  has no `osv` job, because a gate that fails on a backlog somebody else is
  already clearing is noise rather than information.
- **Signing.** The macOS build is unsigned and the Android build is
  debug-signed, because there is no Apple Developer ID and no release keystore.
  Both are stated in the artifact names and the release notes rather than
  discovered on install. A debug-signed APK cannot be replaced in place by a
  release-signed one later, so this decides the upgrade path for anyone who
  installs one.
- **Intel macOS and 32-bit Android** are not built. Each is one matrix entry
  when somebody needs it; neither is worth doubling the workflow's cost on
  speculation.
- **The user interface is analysed, but not by CodeQL.** CodeQL has no Dart
  extractor and `flutter/` is 357 of this repository's files, so `ui.yml` runs
  `flutter analyze` against the same SDK the release builds with. It runs
  `--no-fatal-infos --no-fatal-warnings`, which means it fails on errors only:
  it catches a broken bridge or a real type error, and says nothing about
  style. Narrowing that is work, not a decision already taken.

## Verification

```bash
python3 scripts/brand.py --check
python3 scripts/configure.py --check
python3 scripts/check_protocol_parity.py
cargo test --locked --all-targets --manifest-path libs/hbb_common/Cargo.toml
```

## CI

Every reusable call is pinned to `NDDev-OpenNetwork/ci-workflows` by full SHA
and runs on GitHub-hosted runners. That is a rule, not a fallback: a public
repository must never reach private self-hosted capacity, and public standard
runners are unmetered.

The Rust toolchain is pinned to 1.98 in `build.yml`, and `ui.yml` must declare
the same version — the `contracts` job fails when the two drift, because an
analysis run against a toolchain nothing releases is a green check that proves
nothing. This diverges from upstream deliberately. Upstream pins 1.75 because
the sciter binding stops working on the i128 ABI change in 1.78; this product
ships the Flutter interface on all three platforms and never starts that UI.
Staying on 1.75 has a cost that does bind: cargo 1.75 cannot parse a manifest
declaring edition 2024, and fails while downloading rather than while
compiling, so any dependency that has moved to that edition is unacceptable no
matter what it fixes. On 2026-09-02 that was blocking a quinn-proto security
update, through `rand_core 0.10.1`.

`commitlint.config.mjs` exists for the same reason: the stock
`body-max-line-length` of 100 is unsatisfiable for the 144-character compare
link Dependabot writes into every git-ref bump. The limit is kept and measured
over what could have been wrapped — a line is exempt only when one of its own
tokens is longer than the limit.

## Governance

`.gds/repository.yaml` declares this repository's identity, portfolio, policy
profiles and required verification commands. It is the source; anything under
`.gds/` carrying a `GENERATED FILE` header is a projection and is never edited
by hand.
