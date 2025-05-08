import json

import pytest

from rest_framework.test import APIClient

from tariffs.models import Distributor
from tests.test_utils import create_objects_test_utils, dicts_test_utils

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
        }

    def test_can_create_the_same_distributor_for_different_universities(self):
        dis_1 = {"name": "Dis 1", "cnpj": "00038174000143"}
        dis_2 = {"name": "Dis 2", "cnpj": "00038174000143"}

        Distributor.objects.create(**dis_1)
        Distributor.objects.create(**dis_2)

    def test_can_create_distributors_for_different_universities(self):
        dis_1 = {"name": "Dis 1", "cnpj": "01083200000118"}
        dis_2 = {"name": "Dis 2", "cnpj": "01083200000118"}

        Distributor.objects.create(**dis_1)
        Distributor.objects.create(**dis_2)
