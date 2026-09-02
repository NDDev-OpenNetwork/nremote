# AGENTS.md — nremote

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
- **82 advisories in the application lockfile.** Measured 2026-09-02 with
  osv-scanner over `Cargo.lock`; many have fixes available. There is one
  lockfile — `libs/hbb_common` is a workspace member, not an independent crate
  — so there is nothing smaller to scan honestly. They are not addressed
  because there is no build in CI to verify an update against, and a lockfile
  update nothing compiles is a change nobody can vouch for. `security.yml`
  therefore has no `osv` job and says why in its place; `dependency-review`
  holds the line against anything a pull request introduces. The build workflow
  is what unblocks this.
- **A full application build in CI.** `ci.yml` proves what is true of the
  source on any platform. The three-platform build is `build.yml`'s job.

- **The user interface is not statically analysed.** CodeQL has no Dart
  extractor, and `flutter/` is 357 of this repository's files. `dart analyze`
  is the tool that exists for it and is not wired up; that is a gap with a
  name, not a decision.

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

## Governance

`.gds/repository.yaml` declares this repository's identity, portfolio, policy
profiles and required verification commands. It is the source; anything under
`.gds/` carrying a `GENERATED FILE` header is a projection and is never edited
by hand.
