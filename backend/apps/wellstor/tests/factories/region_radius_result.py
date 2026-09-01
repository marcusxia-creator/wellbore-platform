import factory

from apps.wellstor.models import RegionRadiusResult

from .substation import SubstationFactory


class RegionRadiusResultFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RegionRadiusResult

    substation = factory.SubFactory(SubstationFactory)
    radius_m = 5000.0
    well_count = 40
    good_count = 12
    total_volume = 5000.0
    suitable_probability = 0.82
    substation_candidate = True
    prediction_source = "model"
    model_version = "v1"
