from __future__ import annotations

import re
from typing import Any

_BUSINESS_TIERS = {
    "s": (1.5, 100), "s+": (2.3, 125), "sm": (4, 200),
    "m": (6.5, 400), "m+": (8, 400), "ml": (10, 500),
    "l": (23, 1000), "l+": (25.5, 1500), "xl": (45.5, 1500),
}
_SKY_TIERS = {
    "bronze": ("30GB Anytime", 30 * 1024, 1600),
    "silver": ("50GB Anytime", 50 * 1024, 4500),
    "gold": ("100GB Anytime", 100 * 1024, 7500),
    "platinum": ("Uncapped (200GB FUP)", None, 10000),
}


def _mb(gigabytes: float) -> int:
    return round(gigabytes * 1024)


def plan_benefits(price_plan: str) -> dict[str, Any]:
    name = " ".join(str(price_plan or "").split())
    lowered = name.lower()
    benefits: dict[str, Any] = {
        "data_mb": None, "voice_minutes": None, "sms_count": None,
        "speed_mbps": None, "data_label": "Confirm with MTN",
        "minutes_label": "Confirm with MTN", "sms_label": "Confirm with MTN",
        "summary": "Plan benefits are confirmed during application.",
    }
    sky_tier = next((tier for tier in _SKY_TIERS if tier in lowered and "sky" in lowered), None)
    if sky_tier:
        data_label, data_mb, minutes = _SKY_TIERS[sky_tier]
        benefits.update(data_mb=data_mb, voice_minutes=minutes, sms_count=400,
                        data_label=data_label, minutes_label=f"{minutes:,} all-net",
                        sms_label="400 per day",
                        summary="Anytime data, all-net minutes, daily local SMS allowance and Sky benefits.")
        return benefits
    tier_match = re.fullmatch(r"(?:mtn )?made for business (s\+|sm|m\+|ml|l\+|xl|s|m|l)", lowered)
    if tier_match:
        data_gb, minutes = _BUSINESS_TIERS[tier_match.group(1)]
        benefits.update(data_mb=_mb(data_gb), voice_minutes=minutes,
                        data_label=f"{data_gb:g}GB total", minutes_label=f"{minutes:,} all-net",
                        sms_label="Plan-rated SMS",
                        summary="Total monthly value includes the current MTN Business promotional allocation.")
        return benefits
    flexible_match = re.search(r"made for business value (?:topup\s*)?(\d+)", lowered)
    if flexible_match:
        flexible = f"R{flexible_match.group(1)} flexible value"
        benefits.update(data_label=flexible, minutes_label=flexible, sms_label=flexible,
                        summary="Flexible airtime can be used for data, calls, SMS or eligible bundles.")
        return benefits
    speed_match = re.search(r"(\d+)\s*mbps", lowered)
    if speed_match:
        speed = int(speed_match.group(1))
        benefits.update(speed_mbps=speed,
                        data_label="Uncapped" if "uncapped" in lowered or "unboxed" in lowered else "Business internet",
                        minutes_label="Data-only", sms_label="Data-only",
                        summary=f"Business internet service at up to {speed}Mbps; coverage and fair-use terms apply.")
        return benefits
    data_match = re.search(r"(?:\(|\s)(\d+(?:\.\d+)?)\s*gb(?:\)|\s|$)", lowered)
    if data_match:
        data_gb = float(data_match.group(1))
        benefits.update(data_mb=_mb(data_gb), data_label=f"{data_gb:g}GB Anytime",
                        minutes_label="Data-only", sms_label="Data-only",
                        summary="Monthly data plan; voice and SMS are not included unless MTN confirms otherwise.")
        return benefits
    if "made for executive" in lowered:
        benefits.update(data_label="Premium inclusive data", minutes_label="Inclusive all-net minutes",
                        sms_count=400, sms_label="400 per day",
                        summary="Executive plan with data, all-net minutes, daily SMS allowance and roaming value.")
    elif "mega gigs" in lowered:
        benefits.update(data_label="Data-led allowance", minutes_label="Plan-rated minutes",
                        sms_label="Plan-rated SMS",
                        summary="MTN Business Mega Gigs tier; final inclusive values are confirmed during application.")
    elif "mega talk" in lowered:
        benefits.update(data_label="Plan-rated data", minutes_label="Voice-led allowance",
                        sms_label="Plan-rated SMS",
                        summary="MTN Business Mega Talk tier; final inclusive values are confirmed during application.")
    elif "uncapped" in lowered:
        benefits.update(data_label="Uncapped", minutes_label="Data-only", sms_label="Data-only",
                        summary="Uncapped business internet; fair-use and coverage terms apply.")
    elif "made to share" in lowered:
        benefits.update(data_label="Shared allowance", minutes_label="Shared plan value",
                        sms_label="Plan-rated SMS",
                        summary="Shared business plan; final inclusive values are confirmed during application.")
    elif "business access" in lowered:
        benefits.update(data_label="Business mobile access", minutes_label="Plan-rated minutes",
                        sms_label="Plan-rated SMS",
                        summary="Business access plan; final inclusive values are confirmed during application.")
    return benefits
