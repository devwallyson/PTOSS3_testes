import pytest

from universities.models import ConsumerUnit


@pytest.fixture
def consumer_unit_a(db, university_a):
    return ConsumerUnit.objects.create(
        name="Consumer Unit A",
        code="123456789",
        is_active=True,
        university=university_a,
    )
