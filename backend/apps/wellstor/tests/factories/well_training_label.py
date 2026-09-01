import factory

from apps.wellstor.models import WellTrainingLabel


class WellTrainingLabelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WellTrainingLabel

    base_uwi = factory.Sequence(lambda n: f"UWI-{n:06d}")
    label = 1
    source_file = "training_set.xlsx"
