import json

from rest_framework import status

from tests.fixtures import consumer_unit_a, university_a, university_b, user_a, user_b
from tests.fixtures.distributor import distributor_a


class TestConsumerUnitConstraints:

    endpoint = "/api/consumer-units/"

    def test_reject_duplicate_name_same_university(self, client, user_a, consumer_unit_a):
        client.force_authenticate(user_a)
        response = client.post(
            self.endpoint,
            {
                "name": consumer_unit_a.name,
                "code": "123",
                "university": consumer_unit_a.university.id,
                "total_installed_power": 100,
                "is_active": True,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data
        assert (
            response.data["non_field_errors"][0]
            == "The fields university, name must make a unique set."
        )

    def test_reject_duplicate_code_same_university(self, client, user_a, consumer_unit_a):
        client.force_authenticate(user_a)
        response = client.post(
            self.endpoint,
            {
                "name": "Consumer Unit B",
                "code": consumer_unit_a.code,
                "university": consumer_unit_a.university.id,
                "total_installed_power": 100,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data
        assert (
            response.data["non_field_errors"][0]
            == "The fields university, code must make a unique set."
        )

    def test_allow_duplicate_name_different_universities(self, client, user_b, consumer_unit_a, university_b):
        client.force_authenticate(user_b)
        response = client.post(
            self.endpoint,
            {
                "name": consumer_unit_a.name,
                "code": "123",
                "university": university_b.id,
                "total_installed_power": 100,
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == consumer_unit_a.name
        assert response.data["university"] == university_b.id
        assert response.data["code"] == "123"

    def test_allow_duplicate_code_different_universities(self, client, user_b, consumer_unit_a, university_b):
        client.force_authenticate(user_b)
        response = client.post(
            self.endpoint,
            {
                "name": "Consumer Unit B",
                "code": consumer_unit_a.code,
                "university": university_b.id,
                "total_installed_power": 100,
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["code"] == consumer_unit_a.code
        assert response.data["university"] == university_b.id
        assert response.data["name"] == "Consumer Unit B"

class TestTariffFlagSubgroup:

    endpoint = "/api/consumer-units/create_consumer_unit_and_contract/"

    def test_create_contract_tariff_flag_missing(self, client, user_a, distributor_a, university_a):
        client.force_authenticate(user_a)
        create_consumer = {
            "consumer_unit": {
                "name": "Unb",
                "code": "00540",
                "is_active": True,
                "university": university_a.id,
                "totalInstalledPower": "null"
            },
            "contract_data": {
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "subgroup": "A2",
                "distributor": distributor_a.id,
                "peak_contracted_demand_in_kw": 33,
                "off_peak_contracted_demand_in_kw": 33,
            }
        }
        response = client.post(self.endpoint, create_consumer, format="json")
        print(response.content)  # Log temporário
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert json.loads(response.content) == {'contract': ['This field is required.']}

    def test_create_contract_invalid_tariff_flag(self, client, user_a, distributor_a, university_a):
        client.force_authenticate(user_a)
        valid_tariff_flag = ["G", "B"]
        create_consumer = {
            "consumer_unit": {
                "name": "Unb",
                "code": "00540",
                "is_active": True,
                "university": university_a.id,
                "totalInstalledPower": "null"
            },
            "contract_data": {
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "subgroup": "A2",
                "tariff_flag": "X",
                "distributor": distributor_a.id,
                "peak_contracted_demand_in_kw": 33,
                "off_peak_contracted_demand_in_kw": 33,
            }
        }
        response = client.post(self.endpoint, create_consumer, format="json")
        print(response.content)  # Log temporário
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert json.loads(response.content) == {'contract': ['This field is required.']}

    def test_create_contract_subgroup_missing(self, client, user_a, distributor_a, university_a):
        client.force_authenticate(user_a)
        create_consumer = {
            "consumer_unit": {
                "name": "Unb",
                "code": "00540",
                "is_active": True,
                "university": university_a.id,
                "totalInstalledPower": "null"
            },
            "contract_data": {
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "tariff_flag": "B",
                "distributor": distributor_a.id,
                "peak_contracted_demand_in_kw": 33,
                "off_peak_contracted_demand_in_kw": 33,
            }
        }
        response = client.post(self.endpoint, create_consumer, format="json")
        print(response.content)  # Log temporário
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert json.loads(response.content) == {'contract': ['This field is required.']}

    def test_create_contract_invalid_subgroup(self, client, user_a, distributor_a, university_a):
        client.force_authenticate(user_a)
        create_consumer = {
            "consumer_unit": {
                "name": "Unb",
                "code": "00540",
                "is_active": True,
                "university": university_a.id,
                "totalInstalledPower": "null"
            },
            "contract_data": {
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "subgroup": "A7",
                "tariff_flag": "B",
                "distributor": distributor_a.id,
                "peak_contracted_demand_in_kw": 33,
                "off_peak_contracted_demand_in_kw": 33,
            }
        }
        response = client.post(self.endpoint, create_consumer, format="json")
        print(response.content)  # Log temporário
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert json.loads(response.content) == {'contract': ['This field is required.']}
