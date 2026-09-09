import factory

from apps.wells.models import (
    InjectionDaily,
    InjectionMonthly,
    WellCasing,
    WellCurrentOperator,
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
    cur_operator_name = "Test Operator"
    well_type = "OIL"
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


class WellCurrentOperatorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WellCurrentOperator

    base_uwi = factory.Sequence(lambda n: f"UWI-{n:06d}")
    operator_name = "Test Operator"
    suffix = "00"
    raw_id = factory.Sequence(lambda n: n + 1)


class InjectionDailyFactory(factory.django.DjangoModelFactory):
    """Factory for injection_daily rows.

    The underlying table is unmanaged (created by the import pipeline), so
    tests that use this factory must ensure the table exists — typically by
    running with @pytest.mark.django_db(transaction=True) against a real DB
    that has been seeded with the injection schema.
    """

    class Meta:
        model = InjectionDaily

    base_uwi = factory.Sequence(lambda n: f"UWI-{n:06d}")
    injection_date = factory.Sequence(lambda n: f"2024-{(n % 12) + 1:02d}-01")
    daily_water = 10.0
    daily_gas = 5.0
    daily_steam = 0.0
    injection_pressure = 500.0
    source_file = "test_import.xlsx"


class InjectionMonthlyFactory(factory.django.DjangoModelFactory):
    """Factory for injection_monthly rows.

    The table is unmanaged — see InjectionDailyFactory docstring for the
    same caveat about table existence in tests.
    """

    class Meta:
        model = InjectionMonthly

    base_uwi = factory.Sequence(lambda n: f"UWI-{n:06d}")
    injection_month = factory.Sequence(lambda n: f"2024-{(n % 12) + 1:02d}-01")
    monthly_water = 300.0
    monthly_gas = 150.0
    monthly_steam = 0.0
    cumulative_water = 300.0
    cumulative_gas = 150.0
    cumulative_steam = 0.0
