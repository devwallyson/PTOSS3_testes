import decimal

from datetime import datetime
from decimal import Decimal

import pytest

from django.db import IntegrityError

from contracts.models import EnergyBill
from tests.fixtures import consumer_unit_a, contract_a, distributor_a, university_a


class TestEnergyBillModel:
    def test_create_energy_bill_with_max_consumption(self, consumer_unit_a, contract_a):
        energy_bill = EnergyBill.objects.create(
            consumer_unit=consumer_unit_a,
            contract=contract_a,
            date="2023-01-01",
            anotacoes="Some notes",
            peak_consumption_in_kwh=Decimal("9999999.99"),
            off_peak_consumption_in_kwh=Decimal("9999999.99"),
        )

        assert energy_bill.anotacoes == "Some notes"
        assert energy_bill.peak_consumption_in_kwh == Decimal("9999999.99")
        assert energy_bill.off_peak_consumption_in_kwh == Decimal("9999999.99")
        assert energy_bill.date == datetime.strptime("2023-01-01", "%Y-%m-%d").date()

    def test_create_energy_bill_with_max_measured_demand(self, consumer_unit_a, contract_a):
        energy_bill = EnergyBill.objects.create(
            consumer_unit=consumer_unit_a,
            contract=contract_a,
            date="2023-01-01",
            anotacoes="Some notes",
            peak_measured_demand_in_kw=Decimal("9999999.99"),
            off_peak_measured_demand_in_kw=Decimal("9999999.99"),
        )

        assert energy_bill.anotacoes == "Some notes"
        assert energy_bill.peak_measured_demand_in_kw == Decimal("9999999.99")
        assert energy_bill.off_peak_measured_demand_in_kw == Decimal("9999999.99")
        assert energy_bill.date == datetime.strptime("2023-01-01", "%Y-%m-%d").date()

    def test_create_duplicate_energy_bill(self, consumer_unit_a, contract_a):
        EnergyBill.objects.create(
            consumer_unit=consumer_unit_a,
            contract=contract_a,
            date="2023-01-01",
            anotacoes="Some notes",
        )

        try:
            EnergyBill.objects.create(
                consumer_unit=consumer_unit_a,
                contract=contract_a,
                date="2023-01-01",
                anotacoes="Other notes",
            )
            assert False
        except Exception as e:
            assert str(e) == "Já existe uma fatura cadastrada para este mês."

    def test_create_energy_bill_within_limit_values(self, consumer_unit_a, contract_a):
        energy_bill = EnergyBill.objects.create(
            consumer_unit=consumer_unit_a,
            contract=contract_a,
            date="2023-01-01",
            peak_consumption_in_kwh=Decimal("9999999.99"),
            off_peak_consumption_in_kwh=Decimal("9999999.99"),
            peak_measured_demand_in_kw=Decimal("9999999.99"),
            off_peak_measured_demand_in_kw=Decimal("9999999.99"),
        )

        assert energy_bill.peak_consumption_in_kwh == Decimal("9999999.99")
        assert energy_bill.off_peak_consumption_in_kwh == Decimal("9999999.99")
        assert energy_bill.peak_measured_demand_in_kw == Decimal("9999999.99")
        assert energy_bill.off_peak_measured_demand_in_kw == Decimal("9999999.99")

    def test_exceeding_values_energybill(self, consumer_unit_a, contract_a):
        try:
            EnergyBill.objects.create(
                consumer_unit=consumer_unit_a,
                contract=contract_a,
                date="2023-01-01",
                anotacoes="Some notes",
                peak_consumption_in_kwh=Decimal("10000000.00"),
                off_peak_consumption_in_kwh=Decimal("10000000.00"),
                peak_measured_demand_in_kw=Decimal("10000000.00"),
                off_peak_measured_demand_in_kw=Decimal("10000000.00"),
            )
            assert False
        except decimal.InvalidOperation:
            assert True

    def test_create_energy_invalid_consumption(self, consumer_unit_a, contract_a):
        try:
            EnergyBill.objects.create(
                consumer_unit=consumer_unit_a,
                contract=contract_a,
                date="2024-05-06",
                off_peak_consumption_in_kwh=Decimal("0.00"),
                off_peak_measured_demand_in_kw=Decimal("0.00"),
            )
            assert False
        except Exception as e:
            assert str(e) == "O campo de consumo e demanda não pode ser 0."

    def test_create_energy_bill_invalid_date(self, consumer_unit_a, contract_a):
        try:
            EnergyBill.objects.create(
                consumer_unit=consumer_unit_a,
                contract=contract_a,
                date="invalid_date",
            )
            assert False, "Esperava erro ao criar com data inválida"
        except Exception as e:
            assert str(e) == "Formato de data inválido. Por favor use 'YYYY-MM-DD'."
