import factory

from apps.wellstor.models import Substation


class SubstationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Substation

    facility_code = factory.Sequence(lambda n: f"SUB-{n:04d}")
    facility_name = factory.Sequence(lambda n: f"Substation {n}")
    latitude = 55.0
    longitude = -114.0
    capacity_mw = 100.0
