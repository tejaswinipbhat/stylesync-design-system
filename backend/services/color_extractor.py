import re
import io
import requests
from colorthief import ColorThief
from PIL import Image


def rgb_to_hex(r, g, b):
    return "#{:02x}{:02x}{:02x}".format(r, g, b)


def parse_rgb_string(rgb_str: str):
    """Parse 'rgb(r, g, b)' or 'rgba(r, g, b, a)' to (r, g, b)"""
    match = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", rgb_str)
    if match:
        return int(match.group(1)), int(match.group(2)), int(match.group(3))
    return None


def is_valid_color(rgb_str: str) -> bool:
    """Filter out transparent / near-white / near-black / system defaults"""
    parsed = parse_rgb_string(rgb_str)
    if not parsed:
        return False
    r, g, b = parsed
    # Skip fully transparent, pure white, pure black (common defaults)
    if r == g == b == 0:
        return False
    if r == g == b == 255:
        return False
    # Skip rgba with alpha 0
    if "rgba" in rgb_str and rgb_str.endswith(", 0)"):
        return False
    return True


def luminance(r, g, b):
    """Calculate relative luminance"""
    def c(v):
        v = v / 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * c(r) + 0.7152 * c(g) + 0.0722 * c(b)


def color_distance(c1, c2):
    """Euclidean distance between two RGB tuples"""
    return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5


def deduplicate_colors(colors: list, threshold=30) -> list:
    """Remove near-duplicate colors"""
    unique = []
    for color in colors:
        parsed = parse_rgb_string(color)
        if not parsed:
            continue
        is_dup = any(color_distance(parsed, parse_rgb_string(u)) < threshold
                     for u in unique if parse_rgb_string(u))
        if not is_dup:
            unique.append(color)
    return unique


def categorize_colors(hex_colors: list) -> dict:
    """Classify colors into primary, secondary, accent, background, text, neutrals"""
    rgbs = []
    for h in hex_colors:
        h = h.lstrip("#")
        if len(h) == 6:
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            rgbs.append((r, g, b, h))

    if not rgbs:
        return _default_colors()

    # Sort by luminance
    rgbs_sorted = sorted(rgbs, key=lambda x: luminance(x[0], x[1], x[2]))

    dark_colors = [c for c in rgbs_sorted if luminance(c[0], c[1], c[2]) < 0.15]
    light_colors = [c for c in rgbs_sorted if luminance(c[0], c[1], c[2]) > 0.7]
    mid_colors = [c for c in rgbs_sorted if 0.15 <= luminance(c[0], c[1], c[2]) <= 0.7]

    def to_hex(t):
        return f"#{t[3]}" if len(t) > 3 else rgb_to_hex(t[0], t[1], t[2])

    # Try to find an accent (saturated mid color)
    def saturation(r, g, b):
        mx, mn = max(r, g, b) / 255, min(r, g, b) / 255
        return (mx - mn) / mx if mx != 0 else 0

    saturated = sorted(mid_colors, key=lambda x: saturation(x[0], x[1], x[2]), reverse=True)

    result = {
        "primary": to_hex(dark_colors[0]) if dark_colors else (to_hex(mid_colors[0]) if mid_colors else "#1a1a2e"),
        "secondary": to_hex(mid_colors[0]) if mid_colors else "#4a4a6a",
        "accent": to_hex(saturated[0]) if saturated else "#6c63ff",
        "background": to_hex(light_colors[-1]) if light_colors else "#ffffff",
        "surface": to_hex(light_colors[-2]) if len(light_colors) > 1 else "#f5f5f5",
        "text": to_hex(dark_colors[0]) if dark_colors else "#1a1a1a",
        "textMuted": to_hex(mid_colors[0]) if mid_colors else "#6b7280",
        "border": to_hex(light_colors[0]) if light_colors else "#e5e7eb",
    }

    return result


def _default_colors():
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


def extract_colors_from_image_url(image_url: str, timeout=10) -> list:
    """Download image and extract dominant colors using ColorThief"""
    try:
        resp = requests.get(image_url, timeout=timeout, stream=True,
                            headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            return []

        img_data = io.BytesIO(resp.content)
        ct = ColorThief(img_data)
        palette = ct.get_palette(color_count=6, quality=10)
        return [rgb_to_hex(r, g, b) for r, g, b in palette]
    except Exception:
        return []
