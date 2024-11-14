import pytest

from rest_framework import status

from tests.fixtures import consumer_unit_a, university_a, university_b, user_a, user_b


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
        assert status.HTTP_400_BAD_REQUEST == response.status_code
        assert "non_field_errors" in response.data
        assert "The fields university, name must make a unique set." == response.data["non_field_errors"][0]

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
        assert status.HTTP_400_BAD_REQUEST == response.status_code
        assert "non_field_errors" in response.data
        assert "The fields university, code must make a unique set." == response.data["non_field_errors"][0]

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
        assert status.HTTP_201_CREATED == response.status_code
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
        assert status.HTTP_201_CREATED == response.status_code
        assert response.data["code"] == consumer_unit_a.code
        assert response.data["university"] == university_b.id
        assert response.data["name"] == "Consumer Unit B"
