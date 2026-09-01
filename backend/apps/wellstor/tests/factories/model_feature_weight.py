import factory

from apps.wellstor.models import ModelFeatureWeight


class ModelFeatureWeightFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ModelFeatureWeight

    model_name = "well_selection"
    model_version = "v1"
    feature = factory.Sequence(lambda n: f"feature_{n}")
    weight = 0.5
