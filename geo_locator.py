"""
NSFDC Setu — Geo Locator Backend

Uses the team's odisha_partners.json to:
1. Filter partners by recommended scheme.
2. Optionally filter by partner status.
3. Calculate geodesic distance from the user.
4. Return the nearest partners.

The current uploaded dataset uses:
    fund_utilization_status = "prototype_placeholder"

That status is intentionally NOT treated as "healthy", because it is a
prototype placeholder rather than verified NPA/fund-utilization data.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from geopy.distance import geodesic


BASE_DIR = Path(__file__).resolve().parent
PARTNERS_FILE = BASE_DIR / "data" / "odisha_partners.json"


# ============================================================
# 1. LOAD PARTNER DATA
# ============================================================

def load_partners(path: str | Path = PARTNERS_FILE) -> List[Dict[str, Any]]:
    """Load partner records from odisha_partners.json."""
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Partner file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        partners = json.load(f)

    if not isinstance(partners, list):
        raise ValueError("odisha_partners.json must contain a list.")

    return partners


# ============================================================
# 2. VALIDATE PARTNER DATA
# ============================================================

def _valid_coordinates(partner: Dict[str, Any]) -> bool:
    """Return True if latitude and longitude are valid."""
    try:
        lat = float(partner["lat"])
        lon = float(partner["lon"])
    except (KeyError, TypeError, ValueError):
        return False

    return -90 <= lat <= 90 and -180 <= lon <= 180


# ============================================================
# 3. FILTER BY SCHEME
# ============================================================

def filter_by_scheme(
    scheme_id: str,
    partners: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Keep only partners that handle the requested scheme."""
    if not scheme_id:
        raise ValueError("scheme_id is required.")

    return [
        partner
        for partner in partners
        if scheme_id in partner.get("handles_schemes", [])
        and _valid_coordinates(partner)
    ]


# ============================================================
# 4. FILTER VERIFIED / HEALTHY PARTNERS
# ============================================================

def filter_eligible_partners(
    scheme_id: str,
    partners: List[Dict[str, Any]],
    status_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Filter partners by scheme and optional status.

    Examples:
        status_filter=None
            -> no status exclusion

        status_filter="healthy"
            -> only explicitly healthy partners

    IMPORTANT:
    The current dataset uses "prototype_placeholder" for every partner.
    Therefore a normal production-style "healthy" filter would return zero
    partners. The default is therefore None so the prototype can still
    demonstrate location routing honestly.
    """
    eligible = filter_by_scheme(scheme_id, partners)

    if status_filter is not None:
        eligible = [
            partner
            for partner in eligible
            if partner.get("fund_utilization_status") == status_filter
        ]

    return eligible


# ============================================================
# 5. CALCULATE DISTANCE
# ============================================================

def calculate_distance_km(
    user_lat: float,
    user_lon: float,
    partner_lat: float,
    partner_lon: float,
) -> float:
    """Calculate geodesic straight-line distance in kilometres."""
    try:
        user_lat = float(user_lat)
        user_lon = float(user_lon)
        partner_lat = float(partner_lat)
        partner_lon = float(partner_lon)
    except (TypeError, ValueError):
        raise ValueError("Latitude and longitude must be numeric.")

    if not (-90 <= user_lat <= 90):
        raise ValueError("user_lat must be between -90 and 90.")

    if not (-180 <= user_lon <= 180):
        raise ValueError("user_lon must be between -180 and 180.")

    if not (-90 <= partner_lat <= 90):
        raise ValueError("partner_lat must be between -90 and 90.")

    if not (-180 <= partner_lon <= 180):
        raise ValueError("partner_lon must be between -180 and 180.")

    return round(
        geodesic(
            (user_lat, user_lon),
            (partner_lat, partner_lon)
        ).km,
        1,
    )


# ============================================================
# 6. FIND NEAREST PARTNERS
# ============================================================

def find_nearest_partners(
    user_lat: float,
    user_lon: float,
    scheme_id: str,
    partners: List[Dict[str, Any]],
    top_n: int = 3,
    status_filter: Optional[str] = None,
) -> List[Tuple[Dict[str, Any], float]]:
    """
    Return nearest eligible partners.

    Each item:
        (partner_dict, distance_km)

    By default, no status filter is applied because the uploaded dataset
    contains "prototype_placeholder" rather than verified health/NPA status.
    """
    if top_n <= 0:
        raise ValueError("top_n must be greater than zero.")

    eligible = filter_eligible_partners(
        scheme_id=scheme_id,
        partners=partners,
        status_filter=status_filter,
    )

    scored = []

    for partner in eligible:
        distance_km = calculate_distance_km(
            user_lat,
            user_lon,
            partner["lat"],
            partner["lon"],
        )
        scored.append((partner, distance_km))

    scored.sort(key=lambda item: item[1])
    return scored[:top_n]


# ============================================================
# 7. FRONTEND-FRIENDLY RESULT
# ============================================================

def get_nearest_partner_results(
    user_lat: float,
    user_lon: float,
    scheme_id: str,
    partners: List[Dict[str, Any]],
    top_n: int = 3,
    status_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """Return a clean dictionary for Streamlit/app.py."""
    results = find_nearest_partners(
        user_lat=user_lat,
        user_lon=user_lon,
        scheme_id=scheme_id,
        partners=partners,
        top_n=top_n,
        status_filter=status_filter,
    )

    return {
        "success": True,
        "scheme_id": scheme_id,
        "user_location": {
            "lat": float(user_lat),
            "lon": float(user_lon),
        },
        "count": len(results),
        "partners": [
            {
                "partner_id": partner.get("partner_id"),
                "name": partner.get("name"),
                "type": partner.get("type"),
                "district": partner.get("district"),
                "address": partner.get("address"),
                "lat": float(partner["lat"]),
                "lon": float(partner["lon"]),
                "distance_km": distance_km,
                "fund_utilization_status": partner.get(
                    "fund_utilization_status"
                ),
                "source": partner.get("source"),
            }
            for partner, distance_km in results
        ],
    }


if __name__ == "__main__":
    partners = load_partners()

    # Example: Bhubaneswar / OSFDC coordinates from the dataset context.
    # Use any user coordinates in the real app.
    result = get_nearest_partner_results(
        user_lat=20.2961,
        user_lon=85.8245,
        scheme_id="MFS",
        partners=partners,
        top_n=3,
    )

    print("Nearest partners:")
    for partner in result["partners"]:
        print(
            f"{partner['name']} ({partner['type']}) — "
            f"{partner['district']} — "
            f"{partner['distance_km']} km"
        )
