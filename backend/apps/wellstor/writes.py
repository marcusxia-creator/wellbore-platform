"""Write layer for the wellstor app.

Holds all database mutations for wellstor-owned tables, keeping them separate
from the read layer in `queries.py`. Callers (management commands, future
ingest tasks) invoke these functions instead of writing ORM calls inline,
enforcing a clear read/write split.

The writable tables in this app are the Django-managed ML tables:
`well_feature`, `wellstor_prediction`, `region_prediction`, etc.
"""

from apps.wellstor.models import WellFeature


def upsert_well_feature(base_uwi: str, metrics: dict) -> tuple[WellFeature, bool]:
    """Persist computed feature metrics for a single well.

    Creates the WellFeature row if it does not exist, otherwise updates only
    the fields present in `metrics`. Returns a (instance, created) tuple
    matching the Django `update_or_create` convention.

    `metrics` keys must be valid WellFeature field names. Callers typically
    pass the output of `apps.wellstor.services.features.compute_well_feature_metrics`.
    """
    obj, created = WellFeature.objects.update_or_create(
        base_uwi=base_uwi,
        defaults=metrics,
    )
    return obj, created


def bulk_upsert_well_features(rows: list[dict]) -> tuple[int, int]:
    """Persist computed feature metrics for many wells.

    Each item in `rows` must contain a `base_uwi` key plus any number of
    valid WellFeature field names. Rows are upserted one by one so that
    `auto_now` / `auto_now_add` timestamps are applied correctly by Django.

    Returns (created_count, updated_count).
    """
    created_count = 0
    updated_count = 0

    for row in rows:
        base_uwi = row.pop("base_uwi")
        _, created = upsert_well_feature(base_uwi, row)
        if created:
            created_count += 1
        else:
            updated_count += 1

    return created_count, updated_count
