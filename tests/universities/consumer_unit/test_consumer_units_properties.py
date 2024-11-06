import json

import pytest

from rest_framework import status
from rest_framework.test import APIClient

from tests.test_utils import create_objects_test_utils, dicts_test_utils

ENDPOINT = "/api/consumer-units/"
EMAIL = "admin@admin.com"
PASSWORD = "admin@admin.com"


@pytest.mark.django_db
class TestConsumerUnitsProperties:
    def setup_method(self):
        self.university_dict = dicts_test_utils.university_dict_1
        self.user_dict = dicts_test_utils.university_user_dict_1

        self.university = create_objects_test_utils.create_test_university(self.university_dict)
        self.user = create_objects_test_utils.create_test_university_user(self.user_dict, self.university)

        self.client = APIClient()
        self.client.login(email=self.user_dict["email"], password=self.user_dict["password"])

        self.distributor_dict = dicts_test_utils.distributor_dict_1
        self.distributor = create_objects_test_utils.create_test_distributor(self.distributor_dict, self.university)

        self.consumer_unit_test_1_dict = dicts_test_utils.consumer_unit_dict_1
        self.consumer_unit_test_1 = create_objects_test_utils.create_test_consumer_unit(
            self.consumer_unit_test_1_dict, self.university
        )

        self.consumer_unit_test_2_dict = dicts_test_utils.consumer_unit_dict_2
        self.consumer_unit_test_2 = create_objects_test_utils.create_test_consumer_unit(
            self.consumer_unit_test_2_dict, self.university
        )

        self.contract_test_1_dict = dicts_test_utils.contract_dict_1
        self.contract_test_1 = create_objects_test_utils.create_test_contract(
            self.contract_test_1_dict, self.distributor, self.consumer_unit_test_1
        )

        self.contract_test_2_dict = dicts_test_utils.contract_dict_2
        self.contract_test_2 = create_objects_test_utils.create_test_contract(
            self.contract_test_2_dict, self.distributor, self.consumer_unit_test_2
        )

        self.energy_bill_test_1_dict = dicts_test_utils.energy_bill_dict_1
        self.energy_bill_test_1 = create_objects_test_utils.create_test_energy_bill(
            self.energy_bill_test_1_dict, self.contract_test_2, self.consumer_unit_test_2
        )

    def test_read_consumer_unit_properties_no_one_energy_bill_filled(self):
        response = self.client.get(f"{ENDPOINT}{self.consumer_unit_test_1.id}/")
        consumer_unit = json.loads(response.content)

        assert False is consumer_unit["is_current_energy_bill_filled"]
        assert 12 == consumer_unit["pending_energy_bills_number"]
        assert status.HTTP_200_OK == response.status_code

    def test_read_consumer_unit_properties_current_energy_bill_filled_and_all_energy_bills_pending(self):
        response = self.client.get(f"{ENDPOINT}{self.consumer_unit_test_2.id}/")
        consumer_unit_2 = json.loads(response.content)

        assert True is consumer_unit_2["is_current_energy_bill_filled"]
        assert 11 == consumer_unit_2["pending_energy_bills_number"]
        assert status.HTTP_200_OK == response.status_code
