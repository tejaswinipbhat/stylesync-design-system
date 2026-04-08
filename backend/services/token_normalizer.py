"""
Normalizes raw scraped data into structured design tokens.
Handles conflict resolution when merging with locked tokens.
"""

import re
from services.color_extractor import (
    is_valid_color, parse_rgb_string, rgb_to_hex,
    deduplicate_colors, categorize_colors
)

DEFAULT_FONT_STACK = {
    "headingFont": "Inter, system-ui, sans-serif",
    "bodyFont": "Inter, system-ui, sans-serif",
    "monoFont": "JetBrains Mono, monospace",
    "baseSize": "16px",
    "scale": {
        "h1": {"size": "2.5rem", "weight": "700", "lineHeight": "1.2"},
        "h2": {"size": "2rem",   "weight": "700", "lineHeight": "1.25"},
        "h3": {"size": "1.75rem","weight": "600", "lineHeight": "1.3"},
        "h4": {"size": "1.5rem", "weight": "600", "lineHeight": "1.35"},
        "h5": {"size": "1.25rem","weight": "600", "lineHeight": "1.4"},
        "h6": {"size": "1rem",   "weight": "600", "lineHeight": "1.5"},
        "body": {"size": "1rem", "weight": "400", "lineHeight": "1.6"},
        "small": {"size": "0.875rem","weight": "400","lineHeight": "1.5"},
        "caption": {"size": "0.75rem","weight": "400","lineHeight": "1.4"},
    }
}

DEFAULT_SPACING = {
    "unit": 4,
    "scale": [0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96],
    "named": {
        "xs": "4px", "sm": "8px", "md": "16px",
        "lg": "24px", "xl": "32px", "2xl": "48px", "3xl": "64px"
    }
}

DEFAULT_BORDER_RADIUS = {
    "none": "0px", "sm": "4px", "md": "8px",
    "lg": "12px", "xl": "16px", "2xl": "24px", "full": "9999px"
}

DEFAULT_SHADOWS = {
    "sm":  "0 1px 2px rgba(0,0,0,0.05)",
    "md":  "0 4px 6px rgba(0,0,0,0.07)",
    "lg":  "0 10px 15px rgba(0,0,0,0.1)",
    "xl":  "0 20px 25px rgba(0,0,0,0.1)",
    "inner": "inset 0 2px 4px rgba(0,0,0,0.06)"
}


def clean_font_family(font_str: str) -> str:
    """Clean font family string, remove duplicates, normalize quotes"""
    fonts = [f.strip().strip('"').strip("'") for f in font_str.split(",")]
    seen, cleaned = set(), []
    for f in fonts:
        key = f.lower()
        if key not in seen and f:
            seen.add(key)
            cleaned.append(f)
    return ", ".join(cleaned[:3]) if cleaned else "system-ui, sans-serif"


def detect_font_scale(raw_fonts: list, raw_sizes: dict) -> dict:
    """Build a typography token from raw scraped font data"""
    typography = dict(DEFAULT_FONT_STACK)

    if raw_fonts:
        typography["headingFont"] = clean_font_family(raw_fonts[0])
        typography["bodyFont"] = clean_font_family(raw_fonts[1] if len(raw_fonts) > 1 else raw_fonts[0])

    # If we got actual sizes from scraping, use them
    if raw_sizes.get("h1"):
        typography["scale"]["h1"]["size"] = raw_sizes["h1"]
    if raw_sizes.get("body"):
        typography["scale"]["body"]["size"] = raw_sizes["body"]
        typography["baseSize"] = raw_sizes["body"]

    return typography


def extract_spacing_unit(raw_spacing_values: list) -> dict:
    """Infer spacing unit from scraped margin/padding values"""
    spacing = dict(DEFAULT_SPACING)

    if not raw_spacing_values:
        return spacing

    px_vals = []
    for v in raw_spacing_values:
        m = re.match(r"^(\d+)px$", str(v).strip())
        if m:
            px_vals.append(int(m.group(1)))

    if not px_vals:
        return spacing

    from math import gcd
    from functools import reduce
    nonzero = [v for v in px_vals if v > 0 and v <= 64]
    if nonzero:
        base = reduce(gcd, nonzero)
        if 2 <= base <= 8:
            spacing["unit"] = base
            spacing["scale"] = [i * base for i in range(13)]

    return spacing


def normalize_tokens(raw: dict) -> dict:
    """Convert raw scraped output into structured design tokens"""
    raw_colors_list = raw.get("raw_colors", [])
    raw_fonts = raw.get("fonts", [])
    raw_sizes = raw.get("font_sizes", {})
    raw_spacing = raw.get("spacing_values", [])
    raw_radii = raw.get("border_radii", [])
    image_colors = raw.get("image_colors", [])

    valid_css = [c for c in raw_colors_list if is_valid_color(c)]
    deduped = deduplicate_colors(valid_css)
    hex_css = [rgb_to_hex(*parse_rgb_string(c)) for c in deduped if parse_rgb_string(c)]
    all_hex = hex_css + image_colors
    colors = categorize_colors(all_hex[:20]) if all_hex else _default_colors_dict()

    typography = detect_font_scale(raw_fonts, raw_sizes)
    spacing = extract_spacing_unit(raw_spacing)

    border_radius = dict(DEFAULT_BORDER_RADIUS)
    if raw_radii:
        px_radii = sorted(set(
            int(r.replace("px", "")) for r in raw_radii
            if re.match(r"^\d+px$", str(r)) and int(r.replace("px", "")) <= 9999
        ))
        if px_radii:
            if len(px_radii) >= 1:
                border_radius["sm"] = f"{px_radii[0]}px"
            if len(px_radii) >= 2:
                border_radius["md"] = f"{px_radii[1]}px"
            if len(px_radii) >= 3:
                border_radius["lg"] = f"{px_radii[2]}px"

    return {
        "colors": colors,
        "typography": typography,
        "spacing": spacing,
        "borderRadius": border_radius,
        "shadows": DEFAULT_SHADOWS,
    }


def merge_with_locked(new_tokens: dict, locked_tokens: list) -> dict:
    """
    Merge newly scraped tokens with locked tokens.
    Locked tokens take precedence (conflict resolution).
    """
    merged = dict(new_tokens)

    for lock in locked_tokens:
        category = lock["token_category"]
        key = lock["token_key"]
        value = lock["token_value"]

        if category in merged and isinstance(merged[category], dict):
            merged[category][key] = value

    return merged


def _default_colors_dict():
    return {
        "primary": "#1a1a2e",
        "secondary": "#16213e",
        "accent": "#6c63ff",
        "background": "#ffffff",
        "surface": "#f8fafc",
        "text": "#1e293b",
        "textMuted": "#64748b",
        "border": "#e2e8f0",
    }
