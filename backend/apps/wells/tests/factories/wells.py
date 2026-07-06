import factory

from apps.wells.models import (
    WellCasing,
    WellDrilling,
    WellHeader,
    WellLocation,
    WellProductionFormation,
    WellProductionSummary,
    WellStatus,
    WellStatusCategory,
)


class WellHeaderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WellHeader

    base_uwi = factory.Sequence(lambda n: f"UWI-{n:06d}")
    raw_id = factory.Sequence(lambda n: n + 1)
    well_name = factory.Sequence(lambda n: f"Well {n}")
    cur_operator_name = "Test Operator"
    area = "AB"
    well_type = "OIL"
    suffix = "00"
    user_format_well_id = factory.Sequence(lambda n: f"FMT-{n:06d}")
    import_timestamp = "2026-01-01"


class WellLocationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WellLocation

    raw_id = factory.Sequence(lambda n: n + 1)
    base_uwi = factory.SubFactory(WellHeaderFactory)
    latitude = 55.0
    longitude = -114.0
    suffix = "00"


class WellStatusFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WellStatus

    raw_id = factory.Sequence(lambda n: n + 1)
    base_uwi = factory.SubFactory(WellHeaderFactory)
    well_status_text = "Flowing"
    well_status_abrv = "FL"
    suffix = "00"


class WellDrillingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WellDrilling

    raw_id = factory.Sequence(lambda n: n + 1)
    base_uwi = factory.SubFactory(WellHeaderFactory)
    tvd_m = 1000.0
    md_all_wells_m = 1200.0
    suffix = "00"


class WellCasingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WellCasing

    raw_id = factory.Sequence(lambda n: n + 1)
    base_uwi = factory.SubFactory(WellHeaderFactory)
    casing_type = "production"
    casing_size_mm = 177.8
    casing_depth_m = 1000.0
    casing_grade = "J-55"
    suffix = "00"


class WellProductionSummaryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WellProductionSummary

    raw_id = factory.Sequence(lambda n: n + 1)
    base_uwi = factory.SubFactory(WellHeaderFactory)
    prod_status_text = "Producing"
    most_recent_12_mo_total_oil_m3 = 100.0
    most_recent_12_mo_total_gas_e3m3 = 50.0
    most_recent_12_mo_total_wtr_m3 = 10.0
    suffix = "00"


class WellStatusCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WellStatusCategory

    base_uwi = factory.Sequence(lambda n: f"UWI-{n:06d}")
    status_category = "Active"
    actual_status_text = "Flowing"


class WellProductionFormationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WellProductionFormation

    base_uwi = factory.Sequence(lambda n: f"UWI-{n:06d}")
    formation = "Cardium"
    source_value = "Cardium"
    suffix = "00"
