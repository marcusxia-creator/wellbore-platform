"""Idle-well and WellStor-candidate flags, plus orphan/surface-abandonment checks."""

from __future__ import annotations

from datetime import date, datetime

IDLE_THRESHOLD_MONTHS = 12


def _as_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value.strip():
        text = value.strip().replace("_", "-")
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m", "%Y/%m"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
    return None


def months_between(earlier, as_of) -> int | None:
    """Whole-month difference ``(as_of - earlier)`` using year/month only."""
    start = _as_date(earlier)
    end = _as_date(as_of)
    if start is None or end is None:
        return None
    return (end.year - start.year) * 12 + (end.month - start.month)


def idle_well_flag(
    last_prod,
    last_inj,
    as_of=None,
    threshold_months: int = IDLE_THRESHOLD_MONTHS,
) -> tuple[bool, int | None, int | None]:
    """Idle when last production and last injection are both older than ``threshold_months``.

    A missing injection date counts as old. A missing production date does not flag idle.
    Returns ``(idle, months_since_last_prod, months_since_last_inj)``.
    """
    as_of = as_of or date.today()
    months_prod = months_between(last_prod, as_of)
    months_inj = months_between(last_inj, as_of)
    prod_old = months_prod is not None and months_prod > threshold_months
    inj_old_or_none = months_inj is None or months_inj > threshold_months
    return prod_old and inj_old_or_none, months_prod, months_inj


def wellstor_flag(status_text, idle: bool | None) -> bool:
    """True when status text contains ``susp``/``abd``, or the well is already idle."""
    normalized = (status_text or "").lower()
    status_match = "susp" in normalized or "abd" in normalized
    return bool(status_match or idle)


def is_surface_abandoned(surface_abandonment_date) -> bool:
    """True when a surface-abandonment date is populated."""
    return _as_date(surface_abandonment_date) is not None or (
        isinstance(surface_abandonment_date, str) and bool(surface_abandonment_date.strip())
    )


def is_orphan_reclaimed(reclamation_certificate, orphan_abd_status, orphan_rec_status) -> bool:
    """True when reclamation is ``Y`` or either orphan status is ``completed``."""
    cert = str(reclamation_certificate or "").strip().upper()
    abd = str(orphan_abd_status or "").strip().lower()
    rec = str(orphan_rec_status or "").strip().lower()
    return cert == "Y" or abd == "completed" or rec == "completed"
