"""Cálculo de crecimiento a partir de snapshots históricos.

Regla del producto: con menos de 2 mediciones NO se afirma crecimiento.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Growth:
    snapshots: int
    sufficient_data: bool
    views_per_hour_recent: float | None = None  # entre las dos últimas mediciones
    views_per_hour_overall: float | None = None  # entre la primera y la última
    view_delta: int | None = None
    hours_span: float | None = None


def compute_growth(points: list[tuple[datetime, int | None]]) -> Growth:
    pts = sorted((t, v) for t, v in points if v is not None)
    if len(pts) < 2:
        return Growth(snapshots=len(pts), sufficient_data=False)
    (t0, v0), (tp, vp), (tn, vn) = pts[0], pts[-2], pts[-1]
    span = (tn - t0).total_seconds() / 3600
    recent_span = (tn - tp).total_seconds() / 3600
    if span <= 0 or recent_span <= 0:
        return Growth(snapshots=len(pts), sufficient_data=False)
    return Growth(
        snapshots=len(pts),
        sufficient_data=True,
        views_per_hour_recent=round((vn - vp) / recent_span, 2),
        views_per_hour_overall=round((vn - v0) / span, 2),
        view_delta=vn - v0,
        hours_span=round(span, 2),
    )
