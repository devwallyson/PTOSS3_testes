import pytest

from rest_framework import status

from contracts.models import Contract
from tests.fixtures import (
    admin_a,
    admin_b,
    consumer_unit_a,
    consumer_unit_b,
    contract_a,
    contract_b,
    distributor_a,
    distributor_b,
    guest_a,
    sysadmin,
    university_a,
    university_b,
    user_a,
)


@pytest.mark.django_db
class TestContractViewSet:
    def test_contract_list_permission_user(self, client, user_a, consumer_unit_a, consumer_unit_b):
        client.force_authenticate(user=user_a)

        response = client.get("/api/contracts/", {"consumer_unit_id": consumer_unit_a.id}, format="json")
        assert response.status_code == status.HTTP_200_OK

        response = client.get("/api/contracts/", {"consumer_unit_id": consumer_unit_b.id}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_contract_list_permission_admin(self, client, admin_a, consumer_unit_a, consumer_unit_b):
        client.force_authenticate(user=admin_a)

        response = client.get("/api/contracts/", {"consumer_unit_id": consumer_unit_a.id}, format="json")
        assert response.status_code == status.HTTP_200_OK

        response = client.get("/api/contracts/", {"consumer_unit_id": consumer_unit_b.id}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_contract_list_permission_guest(self, client, guest_a, consumer_unit_a, consumer_unit_b):
        client.force_authenticate(user=guest_a)

        response = client.get("/api/contracts/", {"consumer_unit_id": consumer_unit_a.id}, format="json")
        assert response.status_code == status.HTTP_200_OK

        response = client.get("/api/contracts/", {"consumer_unit_id": consumer_unit_b.id}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_contract_list_permission_sysadmin(self, client, sysadmin, consumer_unit_a):
        client.force_authenticate(user=sysadmin)
        response = client.get("/api/contracts/", {"consumer_unit_id": consumer_unit_a.id}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_contract_retrieve_permission_user(self, client, user_a, contract_a, contract_b):
        client.force_authenticate(user=user_a)

        response = client.get(f"/api/contracts/{contract_a.id}/")
        assert response.status_code == status.HTTP_200_OK

        response = client.get(f"/api/contracts/{contract_b.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_contract_retrieve_permission_admin(self, client, admin_a, contract_a, contract_b):
        client.force_authenticate(user=admin_a)

        response = client.get(f"/api/contracts/{contract_a.id}/")
        assert response.status_code == status.HTTP_200_OK

        response = client.get(f"/api/contracts/{contract_b.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_contract_retrieve_permission_guest(self, client, guest_a, contract_a, contract_b):
        client.force_authenticate(user=guest_a)

        response = client.get(f"/api/contracts/{contract_a.id}/")
        assert response.status_code == status.HTTP_200_OK

        response = client.get(f"/api/contracts/{contract_b.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_contract_retrieve_permission_sysadmin(self, client, sysadmin, contract_a):
        client.force_authenticate(user=sysadmin)

        response = client.get(f"/api/contracts/{contract_a.id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_current_contract_user(self, client, user_a, consumer_unit_a, consumer_unit_b):
        client.force_authenticate(user=user_a)

        response = client.get(
            "/api/contracts/get-current-contract-of-consumer-unit/", {"consumer_unit_id": consumer_unit_a.id}
        )
        assert response.status_code == status.HTTP_200_OK

        response = client.get(
            "/api/contracts/get-current-contract-of-consumer-unit/", {"consumer_unit_id": consumer_unit_b.id}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_current_contract_admin(self, client, admin_a, consumer_unit_a, consumer_unit_b):
        client.force_authenticate(user=admin_a)

        response = client.get(
            "/api/contracts/get-current-contract-of-consumer-unit/", {"consumer_unit_id": consumer_unit_a.id}
        )
        assert response.status_code == status.HTTP_200_OK

        response = client.get(
            "/api/contracts/get-current-contract-of-consumer-unit/", {"consumer_unit_id": consumer_unit_b.id}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_current_contract_guest(self, client, guest_a, consumer_unit_a, consumer_unit_b):
        client.force_authenticate(user=guest_a)

        response = client.get(
            "/api/contracts/get-current-contract-of-consumer-unit/", {"consumer_unit_id": consumer_unit_a.id}
        )
        assert response.status_code == status.HTTP_200_OK

        response = client.get(
            "/api/contracts/get-current-contract-of-consumer-unit/", {"consumer_unit_id": consumer_unit_b.id}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_current_contract_sysadmin(self, client, sysadmin, consumer_unit_a):
        client.force_authenticate(user=sysadmin)

        response = client.get(
            "/api/contracts/get-current-contract-of-consumer-unit/", {"consumer_unit_id": consumer_unit_a.id}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_current_contract_missing_param(self, client, user_a):
        client.force_authenticate(user=user_a)

        response = client.get("/api/contracts/get-current-contract-of-consumer-unit/", {}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND
