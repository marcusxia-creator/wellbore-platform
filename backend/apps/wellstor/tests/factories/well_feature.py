import factory

from apps.wellstor.enums import DeepestCasingType, PerforationType
from apps.wellstor.models import WellFeature


class WellFeatureFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WellFeature

    base_uwi = factory.Sequence(lambda n: f"UWI-{n:06d}")
    uwi_suffix = ""
    latitude = 55.0
    longitude = -114.0
    wellstor_flag = True
    perforation_type = PerforationType.PERF
    deepest_casing_type = DeepestCasingType.PRODUCTION
    normalized_available_volume = 100.0
    casing_burst_rating_psi = 3000.0
    usable_air_mass = 24000.0
