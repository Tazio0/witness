from fastapi import APIRouter, HTTPException, Depends, Header, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from jose import jwt, JWTError
import os
from app.core.database import get_db

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-in-production")
ALGORITHM = "HS256"

# How many reports needed before it shows on the map
VISIBILITY_THRESHOLD = 5

# How long a report stays active (in hours)
REPORT_EXPIRY_HOURS = 24


# --- Auth helper ---

def get_current_user(authorization: str = Header(...)):
    """
    Extract and verify the JWT from the Authorization header.
    Flutter will send: Authorization: Bearer <token>
    """
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError()
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
        username = payload["username"]
        return {"id": user_id, "username": username}
    except (ValueError, JWTError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token"
        )


# --- Request/Response models ---

class ReportRequest(BaseModel):
    category_id: int
    title: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    severity: str = "low"  # low, medium, high


class ReportResponse(BaseModel):
    id: int
    category_id: int
    category_name: str
    category_icon: str
    title: str
    description: Optional[str]
    latitude: float
    longitude: float
    vote_count: int
    severity: str
    created_at: str


# --- Routes ---

@router.post("/", status_code=201)
async def submit_report(
    body: ReportRequest,
    user: dict = Depends(get_current_user)
):
    """Submit a new incident report."""
    conn = get_db()
    cursor = conn.cursor()

    expires_at = datetime.utcnow() + timedelta(hours=REPORT_EXPIRY_HOURS)

    cursor.execute("""
        INSERT INTO reports
            (user_id, category_id, title, description, latitude, longitude, severity, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user["id"], body.category_id, body.title, body.description,
        body.latitude, body.longitude, body.severity, expires_at
    ))
    conn.commit()
    report_id = cursor.lastrowid

    # Auto-add a vote for the person who submitted it
    cursor.execute(
        "INSERT OR IGNORE INTO votes (user_id, report_id) VALUES (?, ?)",
        (user["id"], report_id)
    )
    conn.commit()
    conn.close()

    return {"id": report_id, "message": "Report submitted successfully"}


@router.get("/map", response_model=List[ReportResponse])
async def get_map_reports(
    lat: float,
    lng: float,
    radius_km: float = 10.0
):
    """
    Fetch all visible reports near a location.
    Only returns reports that have hit the 5-vote threshold.
    Reports older than 24 hours are excluded.
    """
    conn = get_db()
    cursor = conn.cursor()

    # Simple bounding box filter (good enough for now, upgrade to PostGIS later)
    # 1 degree latitude ≈ 111km
    lat_offset = radius_km / 111.0
    lng_offset = radius_km / (111.0 * abs(0.001 + lat))  # rough correction

    cursor.execute("""
        SELECT
            r.id, r.category_id, c.name as category_name, c.icon as category_icon,
            r.title, r.description, r.latitude, r.longitude,
            r.vote_count, r.severity, r.created_at
        FROM reports r
        JOIN categories c ON r.category_id = c.id
        WHERE r.visible = 1
          AND r.latitude  BETWEEN ? AND ?
          AND r.longitude BETWEEN ? AND ?
          AND (r.expires_at IS NULL OR r.expires_at > CURRENT_TIMESTAMP)
        ORDER BY r.created_at DESC
    """, (
        lat - lat_offset, lat + lat_offset,
        lng - lng_offset, lng + lng_offset
    ))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


@router.post("/{report_id}/vote", status_code=200)
async def vote_on_report(
    report_id: int,
    user: dict = Depends(get_current_user)
):
    """
    Corroborate an existing report (confirm you saw it too).
    Users don't know a threshold exists — they just 'confirm'.
    Once 5 people confirm, the report becomes visible on the map.
    """
    conn = get_db()
    cursor = conn.cursor()

    # Check report exists
    cursor.execute("SELECT id, vote_count FROM reports WHERE id = ?", (report_id,))
    report = cursor.fetchone()
    if not report:
        conn.close()
        raise HTTPException(status_code=404, detail="Report not found")

    # Try to add vote (UNIQUE constraint blocks duplicates)
    try:
        cursor.execute(
            "INSERT INTO votes (user_id, report_id) VALUES (?, ?)",
            (user["id"], report_id)
        )
    except Exception:
        conn.close()
        raise HTTPException(status_code=400, detail="You have already confirmed this report")

    # Increment vote count
    new_count = report["vote_count"] + 1
    cursor.execute(
        "UPDATE reports SET vote_count = ? WHERE id = ?",
        (new_count, report_id)
    )

    # Make visible if threshold reached
    if new_count >= VISIBILITY_THRESHOLD:
        cursor.execute(
            "UPDATE reports SET visible = 1 WHERE id = ?",
            (report_id,)
        )

    conn.commit()
    conn.close()

    return {
        "vote_count": new_count,
        "visible": new_count >= VISIBILITY_THRESHOLD,
        "message": "Report confirmed"
    }


@router.get("/categories")
async def get_categories():
    """Return all incident categories (for the report form dropdown)."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, icon FROM categories ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
