import json

import pytest

from rest_framework import status
from rest_framework.test import APIClient

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
        self.client.force_authenticate(self.user)

        self.unit1_dict = dicts_test_utils.consumer_unit_dict_1
        self.unit1 = create_objects_test_utils.create_test_consumer_unit(self.unit1_dict, self.university)

        self.unit2_dict = dicts_test_utils.consumer_unit_dict_2
        self.unit2 = create_objects_test_utils.create_test_consumer_unit(self.unit2_dict, self.university)

        self.unit3_dict = dicts_test_utils.consumer_unit_dict_3
        self.unit3 = create_objects_test_utils.create_test_consumer_unit(self.unit3_dict, self.university)

        self.neoenergia_dict = dicts_test_utils.distributor_dict_1
        self.neoenergia = create_objects_test_utils.create_test_distributor(self.neoenergia_dict, self.university)

    # @pytest.mark.skip(reason="Contains errors")
    def test_consumer_units_count_by_distributor(self):
        self.ceb_dict = dicts_test_utils.distributor_dict_2
        self.ceb = create_objects_test_utils.create_test_distributor(self.ceb_dict, self.university)

        self.contract_test_1_dict = dicts_test_utils.contract_dict_1
        self.contract_test_2_dict = dicts_test_utils.contract_dict_2
        self.contract_test_3_dict = dicts_test_utils.contract_dict_3

        self.contract_test_1 = create_objects_test_utils.create_test_contract(
            self.contract_test_1_dict, self.neoenergia, self.unit1
        )
        self.contract_test_2 = create_objects_test_utils.create_test_contract(
            self.contract_test_2_dict, self.ceb, self.unit1
        )
        self.contract_test_3 = create_objects_test_utils.create_test_contract(
            self.contract_test_3_dict, self.ceb, self.unit1
        )

        response = self.client.get(ENDPOINT + f"?university_id={self.university.id}")
        assert status.HTTP_200_OK == response.status_code
        distributors = json.loads(response.content)

        neoenergia = list(filter(lambda dist: dist["id"] == self.neoenergia.id, distributors))[0]
        ceb = list(filter(lambda dist: dist["id"] == self.ceb.id, distributors))[0]

    # @pytest.mark.skip(reason="Not implemented")
    def test_zero_consumer_units_count_by_distributor(self):
        self.ceb_dict = dicts_test_utils.distributor_dict_2
        self.ceb = create_objects_test_utils.create_test_distributor(self.ceb_dict, self.university)

        # garante que não existem contratos vinculados ao distribuidor "ceb"
        assert self.ceb.contracts.count() == 0

        response = self.client.get(ENDPOINT + f"?university_id={self.university.id}")
        assert status.HTTP_200_OK == response.status_code
        distributors = json.loads(response.content)

        neoenergia = list(filter(lambda dist: dist["id"] == self.neoenergia.id, distributors))[0]
        ceb = list(filter(lambda dist: dist["id"] == self.ceb.id, distributors))[0]

        # Verifique se a contagem de unidades consumidoras para "ceb" é igual a zero
        # assert ceb['consumer_units_count'] == 0
