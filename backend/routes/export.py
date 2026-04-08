from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from db import get_connection
import json

router = APIRouter(prefix="/api", tags=["export"])


def _get_tokens(site_id: int) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM design_tokens WHERE site_id = %s ORDER BY id DESC LIMIT 1",
                (site_id,)
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Tokens not found")
            return {
                "colors": row["colors"] or {},
                "typography": row["typography"] or {},
                "spacing": row["spacing"] or {},
                "borderRadius": row["border_radius"] or {},
                "shadows": row["shadows"] or {},
            }


@router.get("/export/{site_id}/css", response_class=PlainTextResponse)
def export_css(site_id: int):
    """Export design tokens as CSS custom properties"""
    try:
        t = _get_tokens(site_id)
        lines = [":root {"]

        colors = t.get("colors", {})
        for key, val in colors.items():
            lines.append(f"  --color-{_kebab(key)}: {val};")

        typo = t.get("typography", {})
        if typo.get("headingFont"):
            lines.append(f"  --font-heading: {typo['headingFont']};")
        if typo.get("bodyFont"):
            lines.append(f"  --font-body: {typo['bodyFont']};")
        if typo.get("baseSize"):
            lines.append(f"  --font-size-base: {typo['baseSize']};")
        scale = typo.get("scale", {})
        for tag, props in scale.items():
            if isinstance(props, dict):
                if props.get("size"):
                    lines.append(f"  --font-size-{tag}: {props['size']};")
                if props.get("weight"):
                    lines.append(f"  --font-weight-{tag}: {props['weight']};")

        spacing = t.get("spacing", {})
        named = spacing.get("named", {})
        for key, val in named.items():
            lines.append(f"  --spacing-{key}: {val};")

        radii = t.get("borderRadius", {})
        for key, val in radii.items():
            lines.append(f"  --radius-{_kebab(key)}: {val};")

        shadows = t.get("shadows", {})
        for key, val in shadows.items():
            lines.append(f"  --shadow-{key}: {val};")

        lines.append("}")
        return "\n".join(lines)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/{site_id}/json")
def export_json(site_id: int):
    """Export design tokens as JSON"""
    try:
        return _get_tokens(site_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/{site_id}/tailwind", response_class=PlainTextResponse)
def export_tailwind(site_id: int):
    """Export design tokens as Tailwind CSS config"""
    try:
        t = _get_tokens(site_id)
        colors = t.get("colors", {})
        typo = t.get("typography", {})
        spacing = t.get("spacing", {})
        radii = t.get("borderRadius", {})

        color_obj = json.dumps(colors, indent=6)
        named_spacing = spacing.get("named", {})
        spacing_obj = json.dumps(named_spacing, indent=6)
        radii_obj = json.dumps({k: v for k, v in radii.items()}, indent=6)

        heading_font = typo.get("headingFont", "system-ui, sans-serif")
        body_font = typo.get("bodyFont", "system-ui, sans-serif")

        config = f"""/** @type {{import('tailwindcss').Config}} */
module.exports = {{
  theme: {{
    extend: {{
      colors: {color_obj},
      spacing: {spacing_obj},
      borderRadius: {radii_obj},
      fontFamily: {{
        heading: ["{heading_font}"],
        body: ["{body_font}"],
      }},
    }},
  }},
  plugins: [],
}};
"""
        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _kebab(s: str) -> str:
    """Convert camelCase to kebab-case"""
    import re
    s = re.sub(r"([A-Z])", r"-\1", s)
    return s.lower().strip("-")
