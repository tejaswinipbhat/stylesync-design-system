from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Any
from db import get_connection
import json

router = APIRouter(prefix="/api", tags=["tokens"])


class TokenUpdateRequest(BaseModel):
    category: str
    key: str
    value: Any


class LockRequest(BaseModel):
    category: str
    key: str
    value: str


@router.get("/tokens/{site_id}")
def get_tokens(site_id: int):
    """Get all design tokens for a site, including lock state"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM design_tokens WHERE site_id = %s ORDER BY id DESC LIMIT 1",
                    (site_id,)
                )
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Tokens not found")

                cur.execute(
                    "SELECT token_category, token_key, token_value FROM locked_tokens WHERE site_id = %s",
                    (site_id,)
                )
                locked = cur.fetchall()

                locked_map = {}
                for lock in locked:
                    cat = lock["token_category"]
                    if cat not in locked_map:
                        locked_map[cat] = {}
                    locked_map[cat][lock["token_key"]] = lock["token_value"]

                return {
                    "site_id": site_id,
                    "colors": row["colors"] or {},
                    "typography": row["typography"] or {},
                    "spacing": row["spacing"] or {},
                    "borderRadius": row["border_radius"] or {},
                    "shadows": row["shadows"] or {},
                    "locked": locked_map,
                }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/tokens/{site_id}")
def update_token(site_id: int, body: TokenUpdateRequest):
    """Update a single token value and record in version history"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Get current value for history
                cur.execute(
                    "SELECT * FROM design_tokens WHERE site_id = %s ORDER BY id DESC LIMIT 1",
                    (site_id,)
                )
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Tokens not found")

                col_map = {
                    "colors": "colors",
                    "typography": "typography",
                    "spacing": "spacing",
                    "borderRadius": "border_radius",
                    "shadows": "shadows",
                }
                col = col_map.get(body.category)
                if not col:
                    raise HTTPException(status_code=400, detail=f"Unknown category: {body.category}")

                current = row[col] or {}
                before_value = current.get(body.key)

                # Update the JSONB key
                cur.execute(
                    f"UPDATE design_tokens SET {col} = {col} || %s::jsonb WHERE site_id = %s",
                    (json.dumps({body.key: body.value}), site_id)
                )

                cur.execute(
                    """INSERT INTO version_history (site_id, token_category, token_key, before_value, after_value, change_type, changes)
                       VALUES (%s, %s, %s, %s, %s, 'edit', %s)""",
                    (site_id, body.category, body.key,
                     json.dumps(before_value), json.dumps(body.value),
                     json.dumps({"category": body.category, "key": body.key,
                                 "before": before_value, "after": body.value}))
                )
                conn.commit()

                return {"success": True, "category": body.category, "key": body.key, "value": body.value}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tokens/{site_id}/lock")
def lock_token(site_id: int, body: LockRequest):
    """Lock a specific token to prevent override on re-scraping"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO locked_tokens (site_id, token_category, token_key, token_value)
                       VALUES (%s, %s, %s, %s)
                       ON CONFLICT (site_id, token_category, token_key)
                       DO UPDATE SET token_value = EXCLUDED.token_value, locked_at = CURRENT_TIMESTAMP""",
                    (site_id, body.category, body.key, body.value)
                )
                cur.execute(
                    """INSERT INTO version_history (site_id, token_category, token_key, after_value, change_type, changes)
                       VALUES (%s, %s, %s, %s, 'lock', %s)""",
                    (site_id, body.category, body.key, body.value,
                     json.dumps({"action": "lock", "category": body.category, "key": body.key}))
                )
                conn.commit()
                return {"success": True, "locked": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tokens/{site_id}/lock/{category}/{key}")
def unlock_token(site_id: int, category: str, key: str):
    """Unlock a previously locked token"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM locked_tokens WHERE site_id = %s AND token_category = %s AND token_key = %s",
                    (site_id, category, key)
                )
                cur.execute(
                    """INSERT INTO version_history (site_id, token_category, token_key, change_type, changes)
                       VALUES (%s, %s, %s, 'unlock', %s)""",
                    (site_id, category, key,
                     json.dumps({"action": "unlock", "category": category, "key": key}))
                )
                conn.commit()
                return {"success": True, "locked": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tokens/{site_id}/history")
def get_version_history(site_id: int, limit: int = 50):
    """Get version history of token changes for a site"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, token_category, token_key, before_value, after_value,
                              change_type, changes, created_at
                       FROM version_history WHERE site_id = %s
                       ORDER BY created_at DESC LIMIT %s""",
                    (site_id, limit)
                )
                rows = cur.fetchall()
                return {"history": [dict(r) for r in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sites")
def get_sites(limit: int = 20):
    """Get recent scraped sites"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, url, title, favicon_url, extraction_status, created_at
                       FROM scraped_sites ORDER BY created_at DESC LIMIT %s""",
                    (limit,)
                )
                rows = cur.fetchall()
                return {"sites": [dict(r) for r in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
