from __future__ import annotations

from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field


PORTAL_BASE_URL = os.getenv("URJA_BASE_URL", "https://urja-ops.flockenergy.tech")
SESSION_TOKEN = os.getenv("URJA_SESSION_TOKEN")


class Meter(BaseModel):
    meter_id: str
    serial_number: str
    make: str
    phase_type: str
    installation_status: str
    transformer_code: str


class Pagination(BaseModel):
    total: int
    page: int
    page_size: int


class MeterSearchResponse(BaseModel):
    data: list[Meter]
    pagination: Pagination


class Location(BaseModel):
    latitude: float
    longitude: float


class EnergyReading(BaseModel):
    timestamp: str
    kwh: float
    kvah: float
    voltage_r: float


class EnergyResponse(BaseModel):
    meter_id: str
    readings: list[EnergyReading]


class MeterDetail(Meter):
    location: Location | None = None


class ErrorResponse(BaseModel):
    code: str
    message: str


app = FastAPI(
    title="Urja Meter API",
    version="1.0.0",
    description=(
        "A clean API facade over the legacy Urja Meter Ops portal. "
        "The portal is treated as read-only."
    ),
)


def headers() -> dict[str, str]:
    h = {"Accept": "application/json"}
    if SESSION_TOKEN:
        h["Cookie"] = f"auth.session_token={SESSION_TOKEN}"
    return h


async def portal_get(path: str, params: dict[str, Any] | None = None) -> Any:
    url = f"{PORTAL_BASE_URL}{path}"
    try:
        async with httpx.AsyncClient(
    timeout=httpx.Timeout(10.0, connect=5.0),
    verify=False
) as client:
            response = await client.get(url, params=params, headers=headers())
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail={"code": "UPSTREAM_TIMEOUT", "message": "Urja portal timed out"},
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "UPSTREAM_UNAVAILABLE", "message": "Urja portal is unavailable"},
        ) from exc

    if response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Resource not found in Urja portal"},
        )
    if response.status_code in (401, 403):
        raise HTTPException(
            status_code=502,
            detail={"code": "UPSTREAM_AUTH_ERROR", "message": "Urja session is missing or expired"},
        )
    if response.status_code >= 500:
        raise HTTPException(
            status_code=503,
            detail={"code": "UPSTREAM_ERROR", "message": "Urja portal returned a server error"},
        )
    response.raise_for_status()
    return response.json()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/v1/meters", response_model=MeterSearchResponse)
async def search_meters(
    q: str = Query("", description="Meter number or serial number"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    raw = await portal_get(
        "/portal/meters/search",
        params={"q": q, "page": page},
    )

    meters = [
        Meter(
            meter_id=item["meterId"],
            serial_number=item["serialNo"],
            make=item["make"],
            phase_type=item["phaseType"],
            installation_status=item["installStatus"],
            transformer_code=item["dtCode"],
        )
        for item in raw.get("data", [])
    ]

    return {
        "data": meters,
        "pagination": {
            "total": raw.get("total", len(meters)),
            "page": raw.get("page", page),
            "page_size": raw.get("pageSize", page_size),
        },
    }


@app.get("/api/v1/meters/{meter_id}", response_model=MeterDetail)
async def get_meter(meter_id: str):
    # The observed portal did not expose a separate Fetch/XHR detail endpoint.
    # Reuse the confirmed search endpoint for the meter's nameplate data.
    raw = await portal_get(
        "/portal/meters/search",
        params={"q": meter_id, "page": 1},
    )
    items = raw.get("data", [])
    if not items or items[0].get("meterId") != meter_id:
        raise HTTPException(
            status_code=404,
            detail={"code": "METER_NOT_FOUND", "message": f"Meter {meter_id} was not found"},
        )

    item = items[0]
    location = None
    try:
        geo = await portal_get(f"/portal/meters/{meter_id}/geo")
        geo_data = geo.get("data", geo)
        location = Location(
            latitude=float(geo_data["latitude"]),
            longitude=float(geo_data["longitude"]),
        )
    except HTTPException:
        # Keep meter metadata available even if geo is temporarily unavailable.
        location = None

    return MeterDetail(
        meter_id=item["meterId"],
        serial_number=item["serialNo"],
        make=item["make"],
        phase_type=item["phaseType"],
        installation_status=item["installStatus"],
        transformer_code=item["dtCode"],
        location=location,
    )


@app.get("/api/v1/meters/{meter_id}/energy", response_model=EnergyResponse)
async def meter_energy(meter_id: str):
    raw = await portal_get(f"/portal/meters/{meter_id}/energy")

    readings = []
    for item in raw.get("data", raw if isinstance(raw, list) else []):
        readings.append(
            EnergyReading(
                timestamp=item["timestamp"],
                kwh=float(item["kwh"]),
                kvah=float(item["kvah"]),
                voltage_r=float(item["voltR"]),
            )
        )

    return {"meter_id": meter_id, "readings": readings}


@app.get("/api/v1/meters/{meter_id}/location", response_model=Location)
async def meter_location(meter_id: str):
    raw = await portal_get(f"/portal/meters/{meter_id}/geo")
    data = raw.get("data", raw)
    return {
        "latitude": float(data["latitude"]),
        "longitude": float(data["longitude"]),
    }
