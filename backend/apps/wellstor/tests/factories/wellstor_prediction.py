import factory

from apps.wellstor.models import WellStorPrediction

from .substation import SubstationFactory


class WellStorPredictionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WellStorPrediction

    base_uwi = factory.Sequence(lambda n: f"UWI-{n:06d}")
    nearest_substation = factory.SubFactory(SubstationFactory)
    distance_m = 2500.0
    airmass = 24000.0
    good_probability = 0.87
    wellstore_candidate = True
    radius_m = 5000.0
    model_version = "v1"
