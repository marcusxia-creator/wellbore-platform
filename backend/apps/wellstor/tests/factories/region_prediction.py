import factory

from apps.wellstor.models import RegionPrediction

from .substation import SubstationFactory


class RegionPredictionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RegionPrediction

    substation = factory.SubFactory(SubstationFactory)
    substation_candidate = True
    suitable_probability = 0.82
    suitable_radius = 5000.0
    well_count = 40
    good_count = 12
    total_volume = 5000.0
    energy_storage_mwh = 3.5
    model_version = "v1"
