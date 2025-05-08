import pytest

from universities.models import University


@pytest.fixture
def university_a(db):
    return University.objects.create(
        name="University of Brasília",
        acronym="UnB",
        cnpj="15989610000137",
    )


@pytest.fixture
def university_b(db):
    return University.objects.create(
        name="University of São Paulo",
        acronym="USP",
        cnpj="47559477000175",
    )


@pytest.fixture
def university_distributors_a(db, university_a, distributor_a):
    university_a.distributors.add(distributor_a)
    return university_a


@pytest.fixture
def university_distributors_b(db, university_b, distributor_b):
    university_b.distributors.add(distributor_b)
    return university_b
