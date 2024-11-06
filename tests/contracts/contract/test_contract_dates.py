import datetime

import pytest

from rest_framework.test import APIClient

from contracts.models import Contract
from tests.test_utils import create_objects_test_utils, dicts_test_utils
from utils.date_util import DateUtils


@pytest.mark.django_db
class TestContractEndpoint:
    def setup_method(self):
        self.university_dict = dicts_test_utils.university_dict_1
        self.user_dict = dicts_test_utils.university_user_dict_1

        self.university = create_objects_test_utils.create_test_university(self.university_dict)
        self.user = create_objects_test_utils.create_test_university_user(self.user_dict, self.university)

        self.client = APIClient()
        self.client.login(email=self.user_dict["email"], password=self.user_dict["password"])

        self.consumer_unit_test_dict = dicts_test_utils.consumer_unit_dict_1
        self.consumer_unit_test = create_objects_test_utils.create_test_consumer_unit(
            self.consumer_unit_test_dict, self.university
        )

        self.consumer_unit_test_dict_without_contract = dicts_test_utils.consumer_unit_dict_4
        self.consumer_unit_test_without_contract = create_objects_test_utils.create_test_consumer_unit(
            self.consumer_unit_test_dict_without_contract, self.university
        )

        self.consumer_unit_test_dict5 = dicts_test_utils.consumer_unit_dict_5
        self.consumer_unit_test_5 = create_objects_test_utils.create_test_consumer_unit(
            self.consumer_unit_test_dict5, self.university
        )

        self.distributor_dict = dicts_test_utils.distributor_dict_1
        self.distributor = create_objects_test_utils.create_test_distributor(self.distributor_dict, self.university)

        self.contract_test_1_dict = dicts_test_utils.contract_dict_1
        self.contract_test_2_dict = dicts_test_utils.contract_dict_2
        self.contract_test_3_dict = dicts_test_utils.contract_dict_3
        self.contract_test_4_dict = dicts_test_utils.contract_dict_4
        self.contract_test_5_dict = dicts_test_utils.contract_dict_5

        self.contract_test_1 = create_objects_test_utils.create_test_contract(
            self.contract_test_1_dict, self.distributor, self.consumer_unit_test
        )
        self.contract_test_2 = create_objects_test_utils.create_test_contract(
            self.contract_test_2_dict, self.distributor, self.consumer_unit_test
        )
        self.contract_test_3 = create_objects_test_utils.create_test_contract(
            self.contract_test_3_dict, self.distributor, self.consumer_unit_test
        )
        self.contract_test_4 = create_objects_test_utils.create_test_contract(
            self.contract_test_4_dict, self.distributor, self.consumer_unit_test
        )
        self.contract_test_5 = create_objects_test_utils.create_test_contract(
            self.contract_test_5_dict, self.distributor, self.consumer_unit_test
        )

    def test_create_contract_and_set_last_contract_end_date_1(self):
        end_date = DateUtils.get_yesterday_date(self.contract_test_2.start_date)

        contract_test_1 = Contract.objects.get(id=self.contract_test_1.id)

        assert contract_test_1.end_date == end_date

    def test_create_contract_and_set_last_contract_end_date_2(self):
        end_date = DateUtils.get_yesterday_date(self.contract_test_3.start_date)

        contract_test_2 = Contract.objects.get(id=self.contract_test_2.id)

        assert contract_test_2.end_date == end_date

    def test_create_contract_and_set_last_contract_end_date_3(self):
        end_date = DateUtils.get_yesterday_date(self.contract_test_4.start_date)

        contract_test_3 = Contract.objects.get(id=self.contract_test_3.id)

        assert contract_test_3.end_date == end_date

    def test_throws_exception_create_contract_with_start_date_not_valid(self):
        with pytest.raises(Exception) as e:
            contract_test_6_dict = dicts_test_utils.contract_dict_6
            create_objects_test_utils.create_test_contract(
                contract_test_6_dict, self.distributor, self.consumer_unit_test
            )

        assert "Novo Contrato não pode ter uma data anterior ou igual ao Contrato atual" in str(e.value)

    def test_contract_with_valid_start_date(self):
        teste = create_objects_test_utils.create_test_contract(
            dicts_test_utils.contract_dict_7, self.distributor, self.consumer_unit_test
        )
        assert teste.check_start_date_is_valid() is None

    def test_contract_with_end_date(self):
        teste = create_objects_test_utils.create_test_contract(
            dicts_test_utils.contract_dict_8, self.distributor, self.consumer_unit_test
        )
        assert teste.check_start_date_is_valid() is None

    def test_consumer_unit_without_contract(self):
        teste = create_objects_test_utils.create_test_contract(
            dicts_test_utils.contract_dict_7, self.distributor, self.consumer_unit_test_without_contract
        )
        assert teste.check_start_date_is_valid() is None

    def test_with_end_date_equals_True(self):
        # CT 1
        teste = create_objects_test_utils.create_test_contract(
            dicts_test_utils.contract_dict_10, self.distributor, self.consumer_unit_test
        )
        teste.end_date = (datetime.date(year=2050, month=2, day=1),)
        assert teste.check_start_date_is_valid() is None

    def test_contract_with_no_end_date_and_consumer_unit_has_no_currecnt_contract(self):
        # CT 2
        teste = create_objects_test_utils.create_test_contract(
            dicts_test_utils.contract_dict_7, self.distributor, self.consumer_unit_test_without_contract
        )
        assert teste.check_start_date_is_valid() is None

        # def test_contract_with_start_date_less_than_current_contract(self):
        #     # data inicial contrato < data inicial do contrato mais antigo da unidade de consumo
        #     # data inicial do contrato menor que a data do contrato atual
        #     # criar um contrato em 2050, outro em 2051 e outro em 2049

        # self = create_objects_test_utils.create_test_contract(
        #     dicts_test_utils.contract_dict_11,
        #     self.distributor,
        #     self.consumer_unit_test_5,
        # )

    #     self.consumer_unit.current_contract = True

    #     with pytest.raises(Exception) as e:
    #         self.check_start_date_is_valid()

    #     assert 'Already have the contract in this date' in str(e.value)
    #     assert self.check_start_date_is_valid() is

    # def test_contract_with_start_date_greater_or_equal_than_oldest_contract(self):
