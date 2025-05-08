import pytest

from tariffs.models import Distributor


@pytest.fixture
def distributor_a(db):
    return Distributor.objects.create(
        name="Distributor A",
        cnpj="34884865000180",
        is_active=True,
    )


@pytest.fixture
def distributor_b(db):
    return Distributor.objects.create(
        name="Distributor B",
        cnpj="12345678000195",
        is_active=True,
    )
