#!/usr/bin/env python3
"""Turn a Craft Anything checkout into Buildflow.

Every change Buildflow makes to a file that upstream owns is made here, never by hand, so that
after merging a new upstream release the whole rebrand can be applied again:

    python3 rebrand/apply.py            # apply (safe to run any number of times)
    python3 rebrand/apply.py --check    # exit 1 if anything is still un-rebranded

Files that only Buildflow has (rebrand/, brand/, docs/UPSTREAM.md, crates/ui-egui/src/flow_theme.rs,
our workflows, README.md, NOTICE additions) are ordinary files and are not touched by this script.

A step that can no longer find the upstream text it edits stops with an error naming the file, so
a changed upstream line is noticed instead of silently skipped. See docs/UPSTREAM.md.
"""

from __future__ import annotations

import re
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

NAME = "Buildflow"
APP_ID = "buildflow"
BUNDLE = "io.github.reachneoagent-commits.buildflow"
REPO = "reachneoagent-commits/buildflow"
REPO_URL = f"https://github.com/{REPO}"
PUBLISHER = "FlowApps"

UP_NAME = "Craft Anything"
UP_BUNDLE = "ai.storyteller.craft-anything"
UP_REPO_URL = "https://github.com/storytold/craft-anything"

CHECK = "--check" in sys.argv
changed: list[str] = []
problems: list[str] = []


def tracked() -> list[Path]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    return [ROOT / p for p in out.decode().split("\0") if p]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, old: str, new: str) -> None:
    if old == new:
        return
    changed.append(str(path.relative_to(ROOT)))
    if not CHECK:
        path.write_text(new, encoding="utf-8", newline="")


def edit(rel: str, pattern: str, repl: str, done: str, *, count: int = 0, flags: int = 0, insert: bool = False) -> None:
    """Replace `pattern` in one file. `done` is text that is present once the edit has been made;
    if neither the pattern nor `done` is found, upstream changed the line and we stop.
    `insert` marks an edit that adds text and leaves its pattern in place: it is made once."""
    path = ROOT / rel
    if not path.exists():
        problems.append(f"{rel}: file is gone (upstream moved or removed it)")
        return
    old = read(path)
    if insert and done in old:
        return
    new, n = re.subn(pattern, repl, old, count=count, flags=flags)
    if n == 0 and done not in old:
        problems.append(f"{rel}: could not find /{pattern}/ to edit, and {done!r} is not there either")
        return
    write(path, old, new)


# --------------------------------------------------------------------------------------------
# 1. The display name, everywhere it is shown or tested.
# --------------------------------------------------------------------------------------------
# Not touched: licences and credits (they must keep naming the original authors), upstream's own
# docs, vendored code, examples, and the Linux/FreeBSD packaging we don't ship.
NAME_SKIP_DIRS = ("vendor/", "docs/", "examples/", "packaging/linux/", "packaging/freebsd/", ".github/", "rebrand/", "brand/", "assets/")
NAME_SKIP_FILES = {"NOTICE", "LICENSE-MIT", "LICENSE-APACHE", "ATTRIBUTION.md", "CONTRIBUTORS.md", "Cargo.lock", "README.md", "about.hbs"}
NAME_EXTS = {".rs", ".tsv", ".toml", ".in", ".wxs", ".wxl", ".ps1", ".sh", ".txt", ".plist", ".html"}
# "…and the Craft Anything contributors" is a copyright line: it stays.
NAME_RE = re.compile(r"Craft Anything(?! contributors)")


def rename_everywhere() -> None:
    for path in tracked():
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(NAME_SKIP_DIRS) or path.name in NAME_SKIP_FILES or path.suffix not in NAME_EXTS:
            continue
        if not path.is_file():
            continue
        try:
            old = read(path)
        except UnicodeDecodeError:
            continue
        new = NAME_RE.sub(NAME, old)
        new = new.replace("ArtCraft Launcher", "FlowApps Launcher")
        write(path, old, new)


# --------------------------------------------------------------------------------------------
# 2. Identity: bundle id, settings folder, keychain entry, update source, links.
# --------------------------------------------------------------------------------------------
def identity() -> None:
    # The window's app id, the Mac bundle and the keychain service. The icon file names under
    # assets/app-icon keep upstream's id on purpose (they are only file names).
    for rel in ("apps/craft-anything/src/main.rs", "packaging/macos/Info.plist.in", "packaging/macos/package.sh", "crates/ai/src/keys.rs"):
        edit(rel, re.escape(UP_BUNDLE), BUNDLE, BUNDLE)

    # Settings, projects and installed engines live in their own folder, so Buildflow and an
    # installed Craft Anything never read each other's files.
    edit("crates/engine/src/settings.rs", r'd\.join\("craft-anything"\)', f'd.join("{APP_ID}")', f'd.join("{APP_ID}")')
    edit("crates/engine/src/settings.rs", r'PathBuf::from\("\.craft-anything"\)', f'PathBuf::from(".{APP_ID}")', f'PathBuf::from(".{APP_ID}")')

    # Where the app looks for its own updates.
    edit(
        "crates/ui-egui/src/updates.rs",
        r'App::new\("craft-anything", "[^"]+", "([^"]+)", "storytold/craft-anything"\)',
        rf'App::new("{APP_ID}", "{NAME}", "\1", "{REPO}")',
        f'"{REPO}")',
    )
    edit("crates/ai/src/openai.rs", re.escape(UP_REPO_URL), REPO_URL, REPO_URL)
    edit("apps/craft-anything-web/src/viewer.rs", re.escape(UP_REPO_URL), REPO_URL, REPO_URL)
    edit("Cargo.toml", r'repository = "[^"]+"', f'repository = "{REPO_URL}"', f'repository = "{REPO_URL}"', count=1)
    edit("packaging/windows/sign.ps1", re.escape(UP_REPO_URL), REPO_URL, REPO_URL)


# --------------------------------------------------------------------------------------------
# 3. Installers: file names, publisher, links, and Windows ids of our own.
# --------------------------------------------------------------------------------------------
def our_guid(theirs: str) -> str:
    """A fixed id of our own for each of upstream's installer ids, so a Buildflow installer never
    upgrades, replaces or shares components with a Craft Anything one."""
    return str(uuid.uuid5(uuid.UUID("6f0f1c0a-7d43-5b7e-9a55-b01d4f10e001"), theirs.upper())).upper()


def installers() -> None:
    mac = "packaging/macos/package.sh"
    edit(mac, r"craft-anything-\$VERSION-macos", f"{APP_ID}-$VERSION-macos", f"{APP_ID}-$VERSION-macos")
    edit(mac, r"craft-anything-cli-\$VERSION-macos", f"{APP_ID}-cli-$VERSION-macos", f"{APP_ID}-cli-$VERSION-macos")
    win = "packaging/windows/package.ps1"
    edit(win, r"craft-anything-\$Version-windows", f"{APP_ID}-$Version-windows", f"{APP_ID}-$Version-windows")
    edit(win, r"craft-anything-<version>-windows", f"{APP_ID}-<version>-windows", f"{APP_ID}-<version>-windows")

    wxs = ROOT / "packaging/windows/craft-anything.wxs"
    old = read(wxs)
    new = old.replace("Learning Machines LLC", PUBLISHER)
    new = re.sub(r"https://getartcraft\.com/apps/craft-anything", REPO_URL, new)
    new = re.sub(r"https://discord\.gg/artcraft", f"{REPO_URL}/issues", new)
    marker = "<!-- Buildflow: installer ids are our own (rebrand/apply.py) -->"
    if marker not in new:
        ids = re.findall(r'(?:UpgradeCode|Guid)="([0-9A-Fa-f-]{36})"', new)
        if not ids:
            problems.append("packaging/windows/craft-anything.wxs: no UpgradeCode or Guid found")
        for theirs in set(ids):
            new = new.replace(theirs, our_guid(theirs))
        new = new.replace("<Wix ", marker + "\n<Wix ", 1)
        if marker not in new:
            problems.append("packaging/windows/craft-anything.wxs: no <Wix element to mark")
    write(wxs, old, new)


# --------------------------------------------------------------------------------------------
# 4. Theme: Buildflow's colours come from crates/ui-egui/src/flow_theme.rs (ours).
# --------------------------------------------------------------------------------------------
THEME_TAIL = '''
// Buildflow (rebrand/apply.py): upstream's themes above are the base; our colours are laid over them.
impl Tokens {
    pub fn for_kind(kind: ThemeKind) -> Self {
        crate::flow_theme::apply(Self::upstream_for_kind(kind))
    }
}
'''


def theme() -> None:
    rel = "crates/ui-egui/src/theme.rs"
    edit(rel, r"pub const BRAND: Color32 = Color32::from_rgb\(0x16, 0x59, 0xc4\);", "pub const BRAND: Color32 = crate::flow_theme::LIME;", "crate::flow_theme::LIME;")
    edit(rel, r"pub fn for_kind\(kind: ThemeKind\) -> Self \{\n        match kind \{", "fn upstream_for_kind(kind: ThemeKind) -> Self {\n        match kind {", "fn upstream_for_kind(")
    path = ROOT / rel
    old = read(path)
    if "crate::flow_theme::apply(" not in old:
        # Before the tests module, so the file still ends with its tests.
        at = old.find("\n#[cfg(test)]\nmod tests {")
        if at < 0:
            problems.append(f"{rel}: no tests module to put our for_kind before")
        else:
            write(path, old, old[:at] + "\n" + THEME_TAIL.rstrip("\n") + "\n" + old[at:])
    edit("crates/ui-egui/src/lib.rs", r"\npub mod first_run;\n", "\npub mod first_run;\npub mod flow_theme;\n", "pub mod flow_theme;", count=1, insert=True)

    # The small browser viewer has its own copy of the colours.
    web = "apps/craft-anything-web/src/viewer.rs"
    edit(web, r"const BRAND: Color32 = Color32::from_rgb\(0x16, 0x59, 0xc4\);", "const BRAND: Color32 = Color32::from_rgb(0xd1, 0xfb, 0x8c);", "from_rgb(0xd1, 0xfb, 0x8c)")
    edit(web, r"const BRAND_INK: Color32 = Color32::from_rgb\(0x74, 0xaa, 0xff\);", "const BRAND_INK: Color32 = Color32::from_rgb(0xd1, 0xfb, 0x8c);", "BRAND_INK: Color32 = Color32::from_rgb(0xd1, 0xfb, 0x8c)")


# --------------------------------------------------------------------------------------------
# 5. One more named provider: NVIDIA NIM.
# --------------------------------------------------------------------------------------------
NIM_ROW = '''    // Buildflow (rebrand/apply.py): NVIDIA NIM's hosted, OpenAI-compatible API.
    Provider {
        name: "NVIDIA NIM",
        kind: BackendKind::OpenaiCompatible,
        base_url: "https://integrate.api.nvidia.com/v1",
        key_env: "NVIDIA_API_KEY",
        alt_key_env: Some("NGC_API_KEY"),
        default_model: "meta/llama-3.3-70b-instruct",
        catalog_id: "nvidia",
    },
];

impl Provider {'''


def providers() -> None:
    edit("crates/ai/src/providers.rs", r"\];\n\nimpl Provider \{", NIM_ROW, "integrate.api.nvidia.com", count=1, insert=True)


# --------------------------------------------------------------------------------------------
# 6. Things upstream ships that Buildflow must not: their trademarked logos, their CI (it needs
#    their signing secrets), their translated READMEs.
# --------------------------------------------------------------------------------------------
REMOVE = [
    "docs/brand",
    ".github/workflows/ci.yml",
    ".github/workflows/freebsd.yml",
    ".github/workflows/packaging-lint.yml",
    ".github/workflows/sonarcloud.yml",
    ".github/workflows/windows-arm64.yml",
    ".github/ISSUE_TEMPLATE",
    ".github/FUNDING.yml",
    ".github/CODEOWNERS",
    ".github/dependabot.yml",
    ".github/pull_request_template.md",
    "sonar-project.properties",
    ".coderabbit.yaml",
]


def remove() -> None:
    import shutil

    targets = [ROOT / r for r in REMOVE] + sorted(ROOT.glob("README.*.md"))
    for path in targets:
        if not path.exists():
            continue
        changed.append(str(path.relative_to(ROOT)) + " (removed)")
        if CHECK:
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


# --------------------------------------------------------------------------------------------
# 7. Notes for people and coding agents working in this fork.
# --------------------------------------------------------------------------------------------
AGENT_NOTE = """<!-- Buildflow (rebrand/apply.py) -->
# Buildflow

This repository is **Buildflow**, a fork of Craft Anything. Read `docs/UPSTREAM.md` first. In short:

- Never hand-edit a file that came from upstream to change branding, ids, colours or links: add the
  change to `rebrand/apply.py` and run it, so it survives the next upstream merge.
- Buildflow's own files are `rebrand/`, `brand/`, `docs/UPSTREAM.md`, `crates/ui-egui/src/flow_theme.rs`,
  `README.md` and `.github/workflows/`.
- Upstream's roadmap, claiming and branch rules below describe how *they* work; they don't bind work
  on this fork. Their engineering rules (never crash, layers, tools, tests) still apply.
- Crate, binary and environment-variable names stay `craft-anything*` / `CRAFT_ANYTHING_*`.

"""


def agent_note() -> None:
    path = ROOT / "CLAUDE.md"
    old = read(path)
    if "<!-- Buildflow (rebrand/apply.py) -->" in old:
        return
    write(path, old, AGENT_NOTE + old)


NOTICE_ADD = """
Buildflow

Buildflow is a modified version of Craft Anything, made by Reach Neo as part of the FlowApps suite.
It changes the name, icon, colours, identifiers and defaults; rebrand/apply.py lists every change.
Buildflow is not affiliated with or endorsed by the ArtCraft Team. The ArtCraft logos are not
included. The Buildflow name and mark (brand/, assets/app-icon/) are not covered by the license
above.
"""

ATTRS_ADD = """
# Buildflow (rebrand/apply.py): files we replace whole keep our version in a merge.
# Needs `git config merge.ours.driver true` once per clone (docs/UPSTREAM.md).
README.md merge=ours
.github/workflows/release.yml merge=ours
"""


def notices() -> None:
    for rel, add, done in (("NOTICE", NOTICE_ADD, "Buildflow is a modified version"), (".gitattributes", ATTRS_ADD, "merge=ours")):
        path = ROOT / rel
        old = read(path)
        if done not in old:
            write(path, old, old.rstrip("\n") + "\n" + add)

    # The trademark paragraph points at docs/brand/, which Buildflow doesn't ship.
    edit(
        "NOTICE",
        r"The ArtCraft name, wordmark and logos in docs/brand/ are trademarks of the ArtCraft Team\. They are\nnot open source and are not covered by the license above; their terms are in\ndocs/brand/LICENSE-brand\.txt\.",
        "The ArtCraft name, wordmark and logos are trademarks of the ArtCraft Team. They are not open\nsource and are not covered by the license above.",
        "wordmark and logos are trademarks",
    )


# The Mac disk image's window background: our colours and name. (Its .tiff and DS_Store are made
# from this by packaging/macos/dmg/generate.py; see docs/UPSTREAM.md.)
def dmg() -> None:
    rel = "packaging/macos/dmg/background.svg"
    edit(rel, r"#4e7bfb", "#d1fb8c", "#d1fb8c")
    for rel in (rel, "packaging/macos/dmg/generate.py", "packaging/macos/dmg/README.md"):
        edit(rel, UP_NAME, NAME, NAME)


def follow_ups() -> None:
    """Places where the name appears in another shape, which the plain rename doesn't reach."""
    # A test's folder name, made from a path that holds the app's name.
    edit("crates/ai/src/cli_agents/mod.rs", r"-home-someone-Craft-Anything-notes-app", "-home-someone-Buildflow-notes-app", "-home-someone-Buildflow-notes-app")


def rustfmt() -> None:
    """A shorter name lets rustfmt join lines; leave the tree formatted the way CI checks it."""
    import shutil

    if CHECK or not changed or not shutil.which("cargo"):
        return
    subprocess.run(["cargo", "fmt", "--all"], cwd=ROOT, check=False)


def main() -> int:
    rename_everywhere()
    follow_ups()
    notices()
    dmg()
    identity()
    installers()
    theme()
    providers()
    remove()
    agent_note()
    rustfmt()

    for p in problems:
        print(f"error: {p}", file=sys.stderr)
    if CHECK:
        for c in changed:
            print(f"not rebranded: {c}")
        return 1 if (changed or problems) else 0
    print(f"{len(changed)} file(s) changed" if changed else "already rebranded: nothing to change")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
