import json

import pytest

from django.db.utils import IntegrityError
from rest_framework import status
from rest_framework.test import APIClient

from tariffs.models import Distributor
from tests.test_utils import create_objects_test_utils, dicts_test_utils
from universities.models import University

ENDPOINT = "/api/distributors/"


@pytest.mark.django_db
class TestTariff:
    def setup_method(self):
        self.university_dict = dicts_test_utils.university_dict_1
        self.user_dict = dicts_test_utils.university_user_dict_1

        self.university = create_objects_test_utils.create_test_university(self.university_dict)
        self.user = create_objects_test_utils.create_test_university_user(self.user_dict, self.university)

        self.client = APIClient()
        self.client.login(email=self.user_dict["email"], password=self.user_dict["password"])

        self.distributor_for_create = {
            "name": "Distribuidora",
            "cnpj": "00038174000143",
            "university": self.university,
        }

    def test_can_create_the_same_distributor_for_different_universities(self):
        dis_1 = {"name": "Dis 1", "cnpj": "00038174000143", "university_id": self.university.id}
        dis_2 = {"name": "Dis 2", "cnpj": "00038174000143", "university_id": self.university.id}
        univ_2 = {"name": "Universidade de Brasília", "cnpj": "00038174000143"}

        University.objects.create(**univ_2)

        Distributor.objects.create(**dis_1)
        with pytest.raises(IntegrityError):
            Distributor.objects.create(**dis_2)

    def test_can_create_distributors_for_different_universities(self):
        university_2 = University.objects.create(name="Universidade de Brasília", cnpj="00038174000143")

        dis_1 = {"name": "Dis 1", "cnpj": "01083200000118", "university": self.university}
        dis_2 = {"name": "Dis 2", "cnpj": "01083200000118", "university": university_2}

        Distributor.objects.create(**dis_1)
        Distributor.objects.create(**dis_2)

    def test_create_distributor_without_name(self):
        distributor_without_name = {"cnpj": "01083200000118", "university": self.university.id}

        response = self.client.post(ENDPOINT, distributor_without_name)
        response_data = json.loads(response.content)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response_data.keys()

    def test_create_distributor_with_duplicate_cnpj(self):
        distributor_1 = {"name": "Dis 1", "cnpj": "01083200000118", "university": self.university}
        distributor_2 = {"name": "Dis 2", "cnpj": "01083200000118", "university": self.university}

        Distributor.objects.create(**distributor_1)
        with pytest.raises(IntegrityError):
            Distributor.objects.create(**distributor_2)
