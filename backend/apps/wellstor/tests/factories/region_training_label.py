import factory

from apps.wellstor.models import RegionTrainingLabel

from .substation import SubstationFactory


class RegionTrainingLabelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RegionTrainingLabel

    substation = factory.SubFactory(SubstationFactory)
    radius_m = 5000.0
    well_counts = 40
    good_count = 12
    region_label = 1
    suitable_radius_m = 5000.0
    source_file = "region_training_data.csv"
