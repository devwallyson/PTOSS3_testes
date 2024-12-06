import json

import pytest

from rest_framework import status
from rest_framework.test import APIClient

from tests.test_utils import create_objects_test_utils, dicts_test_utils
from users.models import CustomUser


@pytest.mark.django_db
class TestContractViewSetTests:
    def setup_method(self):
        self.university_dict = dicts_test_utils.university_dict_1
        self.user_dict = dicts_test_utils.university_user_dict_1
        self.university = create_objects_test_utils.create_test_university(self.university_dict)
        self.user = create_objects_test_utils.create_test_university_user(self.user_dict, self.university)
        self.client = APIClient()
        self.client.login(email=self.user_dict["email"], password=self.user_dict["password"])

        self.distributor_dict = dicts_test_utils.distributor_dict_1
        self.distributor = create_objects_test_utils.create_test_distributor(self.distributor_dict, self.university)

    def test_create_contract_success(self):
        consumer_unit_data = {
            "name": "Faculdade do Gama",
            "code": "111111111",
            "created_on": "2022-10-02",
            "is_active": True,
            "university": self.university.id,
            "total_installed_power": 0.2,
        }
        consumer_unit_response = self.client.post("/api/consumer-units/", consumer_unit_data, format="json")
        created_consumer_unit = json.loads(consumer_unit_response.content)

        assert consumer_unit_response.status_code == status.HTTP_201_CREATED
        assert "id" in created_consumer_unit, f"Chave 'id' ausente em {created_consumer_unit}"

        contract_data = {
            "consumer_unit": created_consumer_unit["id"],
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "subgroup": "A2",
            "distributor": self.distributor.id,
            "peak_contracted_demand_in_kw": 33,
            "off_peak_contracted_demand_in_kw": 33,
        }

        response = self.client.post("/api/contracts/", contract_data, format="json")

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_contract_consumer_unit_not_exist(self):
        contract_data = {
            "consumer_unit": 999,
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "subgroup": "A2",
            "distributor": self.distributor.id,
        }

        response = self.client.post("/api/contracts/", contract_data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in json.loads(response.content), "Expected 'error' in response content"

    def test_create_contract_without_permission(self):
        consumer_unit_data = {
            "name": "Faculdade do Gama",
            "code": "111111111",
            "created_on": "2022-10-02",
            "is_active": True,
            "university": self.university.id,
            "total_installed_power": 9999.99,
        }
        consumer_unit_response = self.client.post("/api/consumer-units/", consumer_unit_data, format="json")
        created_consumer_unit = json.loads(consumer_unit_response.content)

        user_without_permission = CustomUser(email="test2@example.com", type=CustomUser.university_user_type)
        user_without_permission.save()
        self.client.force_authenticate(user=user_without_permission)

        contract_data = {
            "consumer_unit": created_consumer_unit["id"],
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "subgroup": "A2",
            "distributor": self.distributor.id,
        }

        response = self.client.post("/api/contracts/", contract_data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
