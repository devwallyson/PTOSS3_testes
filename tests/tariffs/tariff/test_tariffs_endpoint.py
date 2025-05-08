import json

from datetime import date, timedelta

import pytest

from rest_framework import status
from rest_framework.test import APIClient

from tariffs.models import Distributor, Tariff
from tests.test_utils import create_objects_test_utils, dicts_test_utils

ENDPOINT = "/api/tariffs/"
DATE_FORMAT = "%Y-%m-%d"
TODAY = date.today()


@pytest.mark.django_db
class TestTariffEndpoints:
    def setup_method(self):
        self.university_dict = dicts_test_utils.university_dict_1
        self.user_dict = dicts_test_utils.university_user_dict_1

        self.university = create_objects_test_utils.create_test_university(self.university_dict)
        self.user = create_objects_test_utils.create_test_university_user(self.user_dict, self.university)

        self.client = APIClient()
        self.client.login(email=self.user_dict["email"], password=self.user_dict["password"])

        self.distributor1_dict = dicts_test_utils.distributor_dict_1
        self.distributor1 = create_objects_test_utils.create_test_distributor(self.distributor1_dict, self.university)

    def _create_tariff_dict(
        self, start_date: date = None, end_date: date = None, subgroup: str = "A3", distributor_id: Distributor = None
    ):
        start_date = start_date if start_date is not None else TODAY
        end_date = end_date if end_date is not None else (TODAY + timedelta(days=1))
        distributor_id = distributor_id if distributor_id is not None else self.distributor1.id
        t = {
            "distributor": distributor_id,
            "start_date": start_date.strftime(DATE_FORMAT),
            "end_date": end_date.strftime(DATE_FORMAT),
            "subgroup": subgroup,
            "blue": {
                "peak_tusd_in_reais_per_kw": 1,
                "peak_tusd_in_reais_per_mwh": 2,
                "peak_te_in_reais_per_mwh": 3,
                "off_peak_tusd_in_reais_per_kw": 4,
                "off_peak_tusd_in_reais_per_mwh": 5,
                "off_peak_te_in_reais_per_mwh": 6,
            },
            "green": {
                "peak_tusd_in_reais_per_mwh": 10,
                "peak_te_in_reais_per_mwh": 20,
                "off_peak_tusd_in_reais_per_mwh": 30,
                "off_peak_te_in_reais_per_mwh": 40,
                "na_tusd_in_reais_per_kw": 50,
            },
        }
        return t
