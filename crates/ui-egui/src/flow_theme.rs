//! Buildflow's colours, laid over upstream's two themes.
//!
//! This file is Buildflow's own (upstream has no such file), so it never conflicts in a merge.
//! `rebrand/apply.py` makes `Tokens::for_kind` in `theme.rs` pass upstream's tokens through
//! [`apply`]. The palette is the one in `brand/brand color.png`:
//! lime #D1FB8C, ink #100E0A, paper #F4F5F7, mist #DCE1E1 and white.
//!
//! Lime is a fill, never text on a light surface: text drawn on it is ink, and the light theme's
//! link colour is a deep green that reads on paper. `theme.rs`'s contrast test checks all of it.

use crate::theme::{ThemeKind, Tokens};
use egui::Color32;

/// The app colour.
pub const LIME: Color32 = Color32::from_rgb(0xd1, 0xfb, 0x8c);
/// The brand's near-black.
pub const INK: Color32 = Color32::from_rgb(0x10, 0x0e, 0x0a);
pub const PAPER: Color32 = Color32::from_rgb(0xf4, 0xf5, 0xf7);
pub const MIST: Color32 = Color32::from_rgb(0xdc, 0xe1, 0xe1);

/// Upstream's tokens with Buildflow's colours. Anything not set here (sizes, radii, the danger,
/// warning and success colours, the confidence palette) stays as upstream has it.
pub fn apply(t: Tokens) -> Tokens {
    match t.kind {
        ThemeKind::Studio => Tokens {
            chrome: Color32::from_rgb(0x0b, 0x0a, 0x07),
            canvas: INK,
            card: Color32::from_rgb(0x1a, 0x18, 0x14),
            card_border: Color32::from_rgb(0x34, 0x32, 0x2d),
            raised: Color32::from_rgb(0x21, 0x1f, 0x1a),
            field: Color32::from_rgb(0x21, 0x1f, 0x1b),
            hover: Color32::from_rgb(0x2a, 0x28, 0x23),
            pressed: Color32::from_rgb(0x33, 0x31, 0x2b),
            text: PAPER,
            separator: Color32::from_rgb(0x24, 0x22, 0x1d),
            accent: LIME,
            accent_hover: Color32::from_rgb(0xe0, 0xfd, 0xb0),
            accent_ink: LIME,
            accent_soft: Color32::from_rgba_unmultiplied(0xd1, 0xfb, 0x8c, 40),
            on_accent: INK,
            ..t
        },
        ThemeKind::StudioLight => Tokens {
            chrome: Color32::from_rgb(0xe9, 0xec, 0xec),
            canvas: PAPER,
            card: Color32::WHITE,
            card_border: Color32::from_rgb(0xc9, 0xcf, 0xcf),
            raised: Color32::from_rgb(0xe9, 0xec, 0xec),
            field: Color32::WHITE,
            hover: MIST,
            pressed: Color32::from_rgb(0xd0, 0xd6, 0xd6),
            text: INK,
            separator: MIST,
            code_bg: Color32::from_rgb(0xe9, 0xec, 0xec),
            accent: LIME,
            accent_hover: Color32::from_rgb(0xc0, 0xf0, 0x70),
            accent_ink: Color32::from_rgb(0x3a, 0x5f, 0x00),
            accent_soft: Color32::from_rgba_unmultiplied(0xb4, 0xe8, 0x5a, 70),
            on_accent: INK,
            ..t
        },
    }
}
