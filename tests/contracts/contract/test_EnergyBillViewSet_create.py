import os
import tempfile

from datetime import datetime
from decimal import Decimal

import pytest

from rest_framework import status

from contracts.models import EnergyBill
from tests.fixtures import (
    admin_a,
    admin_b,
    consumer_unit_a,
    consumer_unit_b,
    contract_a,
    contract_b,
    distributor_a,
    distributor_b,
    energy_bill_a,
    guest_a,
    sysadmin,
    university_a,
    university_b,
    user_a,
)


@pytest.mark.django_db
class TestEnergyBillViewSetTests:
    def test_guest_create_energybill(self, guest_a, client, consumer_unit_a, contract_a):
        data = {
            "consumer_unit": consumer_unit_a.id,
            "contract": contract_a.id,
            "date": "2023-01-01",
            "anotacoes": "Some notes",
        }

        client.force_authenticate(user=guest_a)
        response = client.post("/api/energy-bills/", data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_create_energybill(self, user_a, client, consumer_unit_a, contract_a, consumer_unit_b, contract_b):
        data = {
            "consumer_unit": consumer_unit_a.id,
            "contract": contract_a.id,
            "date": "2023-01-01",
            "anotacoes": "Some notes",
        }

        client.force_authenticate(user=user_a)
        response = client.post("/api/energy-bills/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        data["consumer_unit"] = consumer_unit_b.id
        data["contract"] = contract_b.id
        response = client.post("/api/energy-bills/", data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_manager_create_energybill(
        self, admin_a, client, consumer_unit_a, contract_a, consumer_unit_b, contract_b
    ):
        data = {
            "consumer_unit": consumer_unit_a.id,
            "contract": contract_a.id,
            "date": "2023-01-01",
            "anotacoes": "Some notes",
        }

        client.force_authenticate(user=admin_a)
        response = client.post("/api/energy-bills/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        data["consumer_unit"] = consumer_unit_b.id
        data["contract"] = contract_b.id
        response = client.post("/api/energy-bills/", data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_sysadmin_create_energybill(self, sysadmin, client, consumer_unit_a, contract_a):
        data = {
            "consumer_unit": consumer_unit_a.id,
            "contract": contract_a.id,
            "date": "2023-01-01",
        }
        client.force_authenticate(user=sysadmin)
        response = client.post("/api/energy-bills/", data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_sysadmin_update_energybill(self, sysadmin, client, energy_bill_a):
        update_data = {
            "consumer_unit": energy_bill_a.consumer_unit.id,
            "contract": energy_bill_a.contract.id,
            "date": "2023-01-01",
            "anotacoes": "Updated notes by guest",
        }

        client.force_authenticate(user=sysadmin)
        response = client.put(f"/api/energy-bills/{energy_bill_a.id}/", update_data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_guest_update_energybill(self, guest_a, client, energy_bill_a):
        update_data = {
            "consumer_unit": energy_bill_a.consumer_unit.id,
            "contract": energy_bill_a.contract.id,
            "date": "2023-01-01",
            "anotacoes": "Updated notes by guest",
        }

        client.force_authenticate(user=guest_a)
        response = client.put(f"/api/energy-bills/{energy_bill_a.id}/", update_data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_update_energybill_cross_university(self, user_a, client, energy_bill_a, contract_b, consumer_unit_b):
        client.force_authenticate(user=user_a)

        update_data = {
            "consumer_unit": consumer_unit_b.id,
            "contract": energy_bill_a.contract.id,
            "date": "2023-01-01",
            "anotacoes": "Tentativa de mudar unidade",
        }
        response = client.put(f"/api/energy-bills/{energy_bill_a.id}/", update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["consumer_unit"] == energy_bill_a.consumer_unit.id

        update_data = {
            "consumer_unit": energy_bill_a.consumer_unit.id,
            "contract": contract_b.id,
            "date": "2023-01-01",
            "anotacoes": "Tentativa de mudar contrato",
        }
        response = client.put(f"/api/energy-bills/{energy_bill_a.id}/", update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["contract"] == energy_bill_a.contract.id

        update_data = {
            "consumer_unit": energy_bill_a.consumer_unit.id,
            "contract": energy_bill_a.contract.id,
            "date": "2023-01-01",
            "anotacoes": "Atualização permitida",
        }
        response = client.put(f"/api/energy-bills/{energy_bill_a.id}/", update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["anotacoes"] == "Atualização permitida"

    def test_manager_update_energybill_cross_university(
        self, admin_a, client, energy_bill_a, contract_b, consumer_unit_b
    ):
        client.force_authenticate(user=admin_a)

        update_data = {
            "consumer_unit": consumer_unit_b.id,
            "contract": energy_bill_a.contract.id,
            "date": "2023-01-01",
            "anotacoes": "Manager tenta mudar unidade",
        }
        response = client.put(f"/api/energy-bills/{energy_bill_a.id}/", update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["consumer_unit"] == energy_bill_a.consumer_unit.id

        update_data = {
            "consumer_unit": energy_bill_a.consumer_unit.id,
            "contract": contract_b.id,
            "date": "2023-01-01",
            "anotacoes": "Manager tenta mudar contrato",
        }
        response = client.put(f"/api/energy-bills/{energy_bill_a.id}/", update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["contract"] == energy_bill_a.contract.id

        update_data = {
            "consumer_unit": energy_bill_a.consumer_unit.id,
            "contract": energy_bill_a.contract.id,
            "date": "2023-01-01",
            "anotacoes": "Manager atualiza normalmente",
        }
        response = client.put(f"/api/energy-bills/{energy_bill_a.id}/", update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["anotacoes"] == "Manager atualiza normalmente"

    def test_plot_graph_permission_user(self, user_a, client, consumer_unit_a, consumer_unit_b, energy_bill_a):
        data = {"consumer_unit_id": consumer_unit_a.id}

        client.force_authenticate(user=user_a)
        response = client.get("/api/energy-bills/plot-graph/", data=data, format="json")
        assert response.status_code == status.HTTP_200_OK

        data["consumer_unit_id"] = consumer_unit_b.id
        response = client.get("/api/energy-bills/plot-graph/", data=data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_plot_graph_permission_guest(self, guest_a, client, consumer_unit_a, consumer_unit_b, energy_bill_a):
        data = {"consumer_unit_id": consumer_unit_a.id}

        client.force_authenticate(user=guest_a)
        response = client.get("/api/energy-bills/plot-graph/", data=data, format="json")
        assert response.status_code == status.HTTP_200_OK

        data["consumer_unit_id"] = consumer_unit_b.id
        response = client.get("/api/energy-bills/plot-graph/", data=data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_plot_graph_permission_sysadmin(self, sysadmin, client, consumer_unit_a):
        data = {"consumer_unit_id": consumer_unit_a.id}

        client.force_authenticate(user=sysadmin)
        response = client.get("/api/energy-bills/plot-graph/", data=data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_plot_graph_permission_admin(self, admin_a, client, consumer_unit_a, energy_bill_a):
        data = {"consumer_unit_id": consumer_unit_a.id}

        client.force_authenticate(user=admin_a)
        response = client.get("/api/energy-bills/plot-graph/", data=data, format="json")
        assert response.status_code == status.HTTP_200_OK

    def test_plot_graph_missing_consumer_unit_id(self, user_a, client):
        data = {}

        client.force_authenticate(user=user_a)
        response = client.get("/api/energy-bills/plot-graph/", data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "consumer_unit_id is required" in response.json().get("error")
