import pytest

from users.models import UniversityUser


@pytest.fixture
def user_a(db, university_a):
    return UniversityUser.objects.create(
        university=university_a,
        type=UniversityUser.university_admin_user_type,
        email="test@unb.br",
        password="unb",
        first_name="Test",
        last_name="UNB",
        is_seed_user=True,
    )


@pytest.fixture
def user_b(db, university_b):
    return UniversityUser.objects.create(
        university=university_b,
        type=UniversityUser.university_admin_user_type,
        email="test@usp.br",
        password="usp",
        first_name="Test",
        last_name="USP",
        is_seed_user=True,
    )
