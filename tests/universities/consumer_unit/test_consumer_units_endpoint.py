import pytest

from rest_framework import status
from rest_framework.test import APIClient

from tests.test_utils import create_objects_test_utils, dicts_test_utils

ENDPOINT = "/api/consumer-units/"


@pytest.mark.django_db
class TestConsumerUnitsEndpoint:
    def setup_method(self):
        self.university_dict = dicts_test_utils.university_dict_1
        self.user_dict = dicts_test_utils.university_user_dict_1

        self.university = create_objects_test_utils.create_test_university(self.university_dict)
        self.user = create_objects_test_utils.create_test_university_user(self.user_dict, self.university)

        self.client = APIClient()
        self.client.login(email=self.user_dict["email"], password=self.user_dict["password"])

        self.consumer_unit_test_1_dict = dicts_test_utils.consumer_unit_dict_1
        self.consumer_unit_test_1 = create_objects_test_utils.create_test_consumer_unit(
            self.consumer_unit_test_1_dict, self.university
        )

    def test_reject_deleting_consumer_unit(self):
        response = self.client.delete(ENDPOINT, self.consumer_unit_test_1_dict)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_update_is_active_of_consumer_unit_to_false(self):
        self.consumer_unit_test_1_dict["is_active"] = False
        self.consumer_unit_test_1_dict["university"] = self.university.id
        self.consumer_unit_test_1_dict["total_installed_power"] = 12

        response = self.client.put(f"{ENDPOINT}{self.consumer_unit_test_1.id}/", self.consumer_unit_test_1_dict)

        assert response.status_code == status.HTTP_200_OK
