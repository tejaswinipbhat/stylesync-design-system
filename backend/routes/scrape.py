from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from services.scraper import scrape_website
from db import get_connection
import json

router = APIRouter(prefix="/api", tags=["scrape"])


class URLRequest(BaseModel):
    url: str


@router.post("/scrape")
async def scrape(data: URLRequest):
    """Scrape a website and extract design tokens. Saves result to DB."""
    url = data.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    result = await scrape_website(url)

    if "error" in result:
        # Still save the failed attempt
        try:
            _save_site(url, "failed", result.get("error"), None)
        except Exception:
            pass
        return {
            "success": False,
            "error": result["error"],
            "suggestion": _error_suggestion(result["error"])
        }

    # Save to database
    try:
        site_id = _save_site(
            url=result["url"],
            status=result.get("status", "completed"),
            error=None,
            title=result.get("title"),
            favicon_url=result.get("favicon_url"),
            tokens=result.get("tokens", {})
        )
        result["site_id"] = site_id
    except Exception as e:
        print(f"DB save error: {e}")
        result["site_id"] = None

    result["success"] = True
    return result


def _save_site(url, status, error, title=None, favicon_url=None, tokens=None) -> int:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO scraped_sites (url, title, favicon_url, extraction_status, error_message)
                       VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                    (url, title, favicon_url, status, error)
                )
                site_id = cur.fetchone()["id"]

                if tokens:
                    cur.execute(
                        """INSERT INTO design_tokens (site_id, colors, typography, spacing, border_radius, shadows)
                           VALUES (%s, %s, %s, %s, %s, %s)""",
                        (
                            site_id,
                            json.dumps(tokens.get("colors", {})),
                            json.dumps(tokens.get("typography", {})),
                            json.dumps(tokens.get("spacing", {})),
                            json.dumps(tokens.get("borderRadius", {})),
                            json.dumps(tokens.get("shadows", {})),
                        )
                    )
                conn.commit()
                return site_id
    except Exception as e:
        print(f"DB insert error: {e}")
        return -1


def _error_suggestion(error_msg: str) -> str:
    msg = error_msg.lower()
    if "timeout" in msg:
        return "The website took too long to respond. Try again or enter tokens manually."
    if "ssl" in msg or "certificate" in msg:
        return "SSL certificate issue. Try the http:// version of the URL."
    if "403" in msg or "forbidden" in msg:
        return "This website blocks automated scanners. Try entering tokens manually."
    if "404" in msg:
        return "Page not found. Check the URL and try again."
    if "refused" in msg or "connect" in msg:
        return "Could not connect to the website. Check if it's accessible."
    return "Unable to scan this website. You can still enter design tokens manually."
