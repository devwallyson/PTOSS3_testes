import pytest
import json
from rest_framework.test import APIClient
from utils.date_util import DateUtils
from tests.test_utils import dicts_test_utils
from tests.test_utils import create_objects_test_utils
from datetime import datetime
from django.test import TestCase
from rest_framework import status
from contracts.models import EnergyBill
from contracts.models import Contract
from universities.models import ConsumerUnit
from datetime import date

@pytest.mark.django_db
class TestEnergyBillViewSetTests:
    def setup_method(self):
        self.university_dict = dicts_test_utils.university_dict_1
        self.user_dict = dicts_test_utils.university_user_dict_1
        self.university = create_objects_test_utils.create_test_university(self.university_dict)
        self.user = create_objects_test_utils.create_test_university_user(self.user_dict, self.university)
        self.client = APIClient()
        self.client.login(
            email=self.user_dict['email'],
            password=self.user_dict['password'])

        self.distributor_dict = dicts_test_utils.distributor_dict_1
        self.distributor = create_objects_test_utils.create_test_distributor(self.distributor_dict, self.university)

    def test_create_energy_bill_success(self):
        # Crie uma unidade do consumidor
        consumer_unit_data = {
            'name': 'Faculdade do Gama',
            'code': '111111111',
            'created_on': '2022-10-02',
            'is_active': True,
            'university': self.university.id, 
            'total_installed_power': 12
        }
        consumer_unit_response = self.client.post('/api/consumer-units/', consumer_unit_data, format='json')
        created_consumer_unit = json.loads(consumer_unit_response.content)

        assert consumer_unit_response.status_code == status.HTTP_201_CREATED
        assert 'id' in created_consumer_unit, f"Chave 'id' ausente em {created_consumer_unit}"

        # Crie um contrato associado à unidade do consumidor
        contract_data = {
            'consumer_unit': created_consumer_unit['id'],
            'start_date': '2023-01-01',  # Adicione a data de início do contrato
            'end_date': '2023-12-31',    # Adicione a data de término do contrato
            'subgroup': 'A2',
            'distributor': self.distributor.id,
        }
        contract_response = self.client.post('/api/contracts/', contract_data, format='json')
        created_contract = json.loads(contract_response.content)

        print(contract_response.status_code)
        print(contract_response.content)

        assert contract_response.status_code == status.HTTP_201_CREATED
        
        assert 'id' in created_contract, f"Chave 'id' ausente em {created_contract}"

        # Crie uma conta de energia usando a unidade do consumidor e o contrato criados
        data = {
            'consumer_unit': created_consumer_unit['id'],
            'contract': created_contract['id'],
            'date': '2023-01-01',
            'anotacoes': 'Some notes',
        }

        response = self.client.post('/api/energy-bills/', data, format='json')

        print(response.status_code)
        print(response.content)

        assert response.status_code == status.HTTP_201_CREATED

        # Verifique se a conta de energia foi realmente criada no banco de dados
        energy_bill = EnergyBill.objects.get(consumer_unit=created_consumer_unit['id'], date=datetime.strptime('2023-01-01', '%Y-%m-%d').date())
        assert energy_bill.anotacoes == 'Some notes', f"Valor esperado: 'Some notes', Valor atual: {energy_bill.anotacoes}"

    def test_create_energy_bill_invalid_date(self):
        data = {
            'consumer_unit': 1,
            'date': 'invalid_date',
        }

        response = self.client.post('/api/energy-bills/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_energy_invalid_consumption(self):
        data = {
            'consumer_unit': 1,
            'date': '2024-05-06',
            'off_peak_consumption_in_kwh': 0.00,
            'off_peak_measured_demand_in_kw': 0.00
        }

        response = self.client.post('/api/energy-bills/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_energy_bill_long_notes(self):
        data = {
            'consumer_unit': 1,
            'date': '2023-01-01',
            'anotacoes': 'A' * 1001,
        }

        response = self.client.post('/api/energy-bills/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


    def test_create_duplicate_energy_bill(self):
        # Crie uma unidade do consumidor
        consumer_unit_data = {
            'name': 'Faculdade do Gama',
            'code': '111111111',
            'created_on': '2022-10-02',
            'is_active': True,
            'university': self.university.id, 
            'total_installed_power': None
        }
        consumer_unit_response = self.client.post('/api/consumer-units/', consumer_unit_data, format='json')
        created_consumer_unit = json.loads(consumer_unit_response.content)

        assert consumer_unit_response.status_code == status.HTTP_201_CREATED
        assert 'id' in created_consumer_unit, f"Chave 'id' ausente em {created_consumer_unit}"

        # Crie um contrato associado à unidade do consumidor
        contract_data = {
            'consumer_unit': created_consumer_unit['id'],
            'start_date': '2023-01-01',  # Adicione a data de início do contrato
            'end_date': '2023-12-31',    # Adicione a data de término do contrato
            'subgroup': 'A2',
            'distributor': self.distributor.id,
        }
        contract_response = self.client.post('/api/contracts/', contract_data, format='json')
        created_contract = json.loads(contract_response.content)

        print(contract_response.status_code)
        print(contract_response.content)

        assert contract_response.status_code == status.HTTP_201_CREATED
        
        assert 'id' in created_contract, f"Chave 'id' ausente em {created_contract}"

        # Crie uma conta de energia usando a unidade do consumidor e o contrato criados
        data = {
            'consumer_unit': created_consumer_unit['id'],
            'contract': created_contract['id'],
            'date': '2023-01-01',
            'anotacoes': 'Some notes',
        }

        response = self.client.post('/api/energy-bills/', data, format='json')

        print(response.status_code)
        print(response.content)

        assert response.status_code == status.HTTP_201_CREATED

        response = self.client.post('/api/energy-bills/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_max_peak_and_offpeak_consumption_values(self):
        consumer_unit_data = {
            'name': 'Faculdade do Gama',
            'code': '111111111',
            'created_on': '2022-10-02',
            'is_active': True,
            'university': self.university.id, 
            'total_installed_power': 12
        }
        consumer_unit_response = self.client.post('/api/consumer-units/', consumer_unit_data, format='json')
        created_consumer_unit = json.loads(consumer_unit_response.content)

        assert consumer_unit_response.status_code == status.HTTP_201_CREATED
        assert 'id' in created_consumer_unit, f"Chave 'id' ausente em {created_consumer_unit}"

        contract_data = {
            'consumer_unit': created_consumer_unit['id'],
            'start_date': '2023-01-01',  
            'end_date': '2023-12-31',    
            'subgroup': 'A2',
            'distributor': self.distributor.id,
        }
        contract_response = self.client.post('/api/contracts/', contract_data, format='json')
        created_contract = json.loads(contract_response.content)

        print(contract_response.status_code)
        print(contract_response.content)

        assert contract_response.status_code == status.HTTP_201_CREATED
        
        assert 'id' in created_contract, f"Chave 'id' ausente em {created_contract}"

        data = {
            'consumer_unit': created_consumer_unit['id'],
            'contract': created_contract['id'],
            'date': '2023-01-01',
            'anotacoes': 'Some notes',
            'peak_consumption_in_kwh': 9999999.99,
            'off_peak_consumption_in_kwh': 9999999.99,
        }

        response = self.client.post('/api/energy-bills/', data, format='json')

        print(response.status_code)
        print(response.content)

        assert response.status_code == status.HTTP_201_CREATED

        energy_bill = EnergyBill.objects.get(consumer_unit=created_consumer_unit['id'], date=datetime.strptime('2023-01-01', '%Y-%m-%d').date())
        assert energy_bill.anotacoes == 'Some notes', f"Valor esperado: 'Some notes', Valor atual: {energy_bill.anotacoes}"

    def test_max_peak_and_offpeak_measured_values(self):
        consumer_unit_data = {
            'name': 'Faculdade do Gama',
            'code': '111111111',
            'created_on': '2022-10-02',
            'is_active': True,
            'university': self.university.id, 
            'total_installed_power': 12
        }
        consumer_unit_response = self.client.post('/api/consumer-units/', consumer_unit_data, format='json')
        created_consumer_unit = json.loads(consumer_unit_response.content)

        assert consumer_unit_response.status_code == status.HTTP_201_CREATED
        assert 'id' in created_consumer_unit, f"Chave 'id' ausente em {created_consumer_unit}"


        contract_data = {
            'consumer_unit': created_consumer_unit['id'],
            'start_date': '2023-01-01',  
            'end_date': '2023-12-31',    
            'subgroup': 'A2',
            'distributor': self.distributor.id,
        }
        contract_response = self.client.post('/api/contracts/', contract_data, format='json')
        created_contract = json.loads(contract_response.content)

        print(contract_response.status_code)
        print(contract_response.content)

        assert contract_response.status_code == status.HTTP_201_CREATED
        
        assert 'id' in created_contract, f"Chave 'id' ausente em {created_contract}"


        data = {
            'consumer_unit': created_consumer_unit['id'],
            'contract': created_contract['id'],
            'date': '2023-01-01',
            'anotacoes': 'Some notes',
            'peak_measured_demand_in_kw': 9999999.99,
            'off_peak_measured_demand_in_kw': 9999999.99,
        }

        response = self.client.post('/api/energy-bills/', data, format='json')

        print(response.status_code)
        print(response.content)

        assert response.status_code == status.HTTP_201_CREATED


        energy_bill = EnergyBill.objects.get(consumer_unit=created_consumer_unit['id'], date=datetime.strptime('2023-01-01', '%Y-%m-%d').date())
        assert energy_bill.anotacoes == 'Some notes', f"Valor esperado: 'Some notes', Valor atual: {energy_bill.anotacoes}"

    def test_exceeding_values_energybill(self):
        consumer_unit_data = {
            'name': 'Faculdade do Gama',
            'code': '111111111',
            'created_on': '2022-10-02',
            'is_active': True,
            'university': self.university.id, 
            'total_installed_power': 12
        }
        consumer_unit_response = self.client.post('/api/consumer-units/', consumer_unit_data, format='json')
        created_consumer_unit = json.loads(consumer_unit_response.content)

        assert consumer_unit_response.status_code == status.HTTP_201_CREATED
        assert 'id' in created_consumer_unit, f"Chave 'id' ausente em {created_consumer_unit}"

        contract_data = {
            'consumer_unit': created_consumer_unit['id'],
            'start_date': '2023-01-01',  
            'end_date': '2023-12-31',    
            'subgroup': 'A2',
            'distributor': self.distributor.id,
        }
        contract_response = self.client.post('/api/contracts/', contract_data, format='json')
        created_contract = json.loads(contract_response.content)

        print(contract_response.status_code)
        print(contract_response.content)

        assert contract_response.status_code == status.HTTP_201_CREATED
        
        assert 'id' in created_contract, f"Chave 'id' ausente em {created_contract}"

        data = {
            'consumer_unit': created_consumer_unit['id'],
            'contract': created_contract['id'],
            'date': '2023-01-01',
            'anotacoes': 'Some notes',
            'peak_consumption_demand_in_kw': 10000000,
            'off_peak_consumption_demand_in_kw': 10000000,
            'peak_measured_demand_in_kw': 10000000,
            'off_peak_measured_demand_in_kw': 10000000
        }

        response = self.client.post('/api/energy-bills/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        print(response.status_code)
        print(response.content)

        assert "Ensure that there are no more than 7 digits before the decimal point." in response.content.decode('utf-8')



