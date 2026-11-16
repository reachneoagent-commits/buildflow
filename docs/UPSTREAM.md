# Keeping up with upstream

Buildflow is a fork of [Craft Anything](https://github.com/storytold/craft-anything) (MIT or
Apache-2.0). Upstream ships a release every few days. This is how we take their updates without
losing our name, colours and settings.

## The one rule

**Every change Buildflow makes to a file that came from upstream is made by `rebrand/apply.py`,
never by hand.** The script can be run again at any time, so after a merge we can take upstream's
version of any conflicted file and re-apply our changes in one step.

## What lives where

| Ours (upstream has no such file, or we replace theirs whole) | Upstream's, edited only by `rebrand/apply.py` |
|---|---|
| `rebrand/` (the script, the icon source, `upstream.json`) | everything under `crates/`, `apps/`, `packaging/`, `xtask/` |
| `brand/` (logo, colours, `.ai` source) | `assets/app-icon/` (file names theirs, artwork ours: `rebrand/icons.sh`) |
| `crates/ui-egui/src/flow_theme.rs` (all our colours) | `Cargo.toml`, `CLAUDE.md`, `NOTICE`, `.gitattributes` |
| `docs/UPSTREAM.md`, `README.md` | |
| `.github/workflows/release.yml`, `upstream-check.yml`, `pages.yml` | |
| `site/` (the GitHub Pages site) | |

What the script changes, in short: the display name (Craft Anything → Buildflow) wherever it is
shown, the bundle id, the settings folder (`buildflow`, so the two apps never share files), the
keychain entry, where the app looks for updates, installer names and Windows installer ids, the
theme hook, one extra provider (NVIDIA NIM), and it removes upstream's logos, their CI and their
translated READMEs.

What we leave alone on purpose: crate names (`craft-anything-*`), the binaries (`craft-anything`,
`craft-anything-cli`), environment variables (`CRAFT_ANYTHING_*`), the `.cany` project format, the
MCP server name, licences and credits, upstream's own docs, and the Linux and FreeBSD packaging
(we ship macOS and Windows only).

## Weekly check

The **Upstream check** workflow runs every Monday. It compares upstream's newest release tag with
the one in `rebrand/upstream.json`. If there is a newer one it tries the merge and the rebrand in
a scratch checkout and opens an issue saying whether it went through cleanly. It never changes
Buildflow or ships anything: a person does the merge below.

## Merging an upstream release

Set the clone up once, so upstream's tags arrive as `upstream/v…` and never collide with
Buildflow's own release tags (which reuse the version numbers):

```bash
git remote add upstream https://github.com/storytold/craft-anything.git
git config remote.upstream.tagOpt --no-tags
git config --add remote.upstream.fetch '+refs/tags/*:refs/tags/upstream/*'
git config merge.ours.driver true
```

Never push the `upstream/*` tags. Then, for each new release:

```bash
git fetch upstream
git checkout -b upstream-sync
git merge upstream/v0.7.0   # the new upstream tag
```

If there are conflicts:

1. For a file in the right-hand column above, take theirs: `git checkout --theirs -- <file>`.
2. For a file we deleted that they changed ("deleted by us"): keep it deleted, `git rm <file>`.
3. For `README.md` or our workflows, keep ours: `git checkout --ours -- <file>`.

Then re-apply the rebrand and check it:

```bash
python3 rebrand/apply.py
python3 rebrand/apply.py --check     # prints nothing and exits 0 when everything is rebranded
```

If the script stops with `could not find … to edit`, upstream changed that line: open the file,
see what it looks like now and update the pattern in `rebrand/apply.py`. If upstream changed their
icon files, run `rebrand/icons.sh` to put ours back.

Build and test, then set the new tag in `rebrand/upstream.json`, commit and open a pull request:

```bash
cargo build --locked -p craft-anything -p craft-anything-cli
cargo test --locked -p craft-anything-ui-egui -p craft-anything-ai -p craft-anything-engine --no-fail-fast
```

Run the app once and look at it before releasing: tests don't see colours.

## Versions

Buildflow keeps upstream's version number (`[workspace.package] version` in `Cargo.toml`), so
"Buildflow 0.6.1" is built on Craft Anything 0.6.1. A Buildflow-only fix between upstream releases
adds a fourth part to the release tag only if we ever need one; so far we don't.

## Releasing

Actions → Release → Run workflow builds the macOS DMG and the Windows MSI and portable zip and
publishes a GitHub release. Builds are not signed with a paid certificate. The FlowApps launcher
installs and updates Buildflow from those releases.
