<!-- Buildflow (rebrand/apply.py) -->
# Buildflow

This repository is **Buildflow**, a fork of Craft Anything. Read `docs/UPSTREAM.md` first. In short:

- Never hand-edit a file that came from upstream to change branding, ids, colours or links: add the
  change to `rebrand/apply.py` and run it, so it survives the next upstream merge.
- Buildflow's own files are `rebrand/`, `brand/`, `docs/UPSTREAM.md`, `crates/ui-egui/src/flow_theme.rs`,
  `README.md` and `.github/workflows/`.
- Upstream's roadmap, claiming and branch rules below describe how *they* work; they don't bind work
  on this fork. Their engineering rules (never crash, layers, tools, tests) still apply.
- Crate, binary and environment-variable names stay `craft-anything*` / `CRAFT_ANYTHING_*`.

# Craft Anything

The rules below are loaded into every session (imports). They are mandatory for every change: follow them
without being asked, unless the person explicitly says otherwise for a specific task.

@AGENTS.md
@docs/pitfalls.md

The plan and assignments are `docs/ROADMAP.md` (open work: `cargo xtask pending`); what works today is
`docs/STATUS.md` (with `docs/tool-status.md`); where additions go is `docs/extending.md`. Private plans may
live in `plan/` (gitignored) when present.
