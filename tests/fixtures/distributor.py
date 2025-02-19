import pytest

from tariffs.models import Distributor


@pytest.fixture
def distributor_a(db, university_a):
    return Distributor.objects.create(
        name="CEB",
        cnpj = "34884865000180",
        is_active=True,
        university=university_a
    )
