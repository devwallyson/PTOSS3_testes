from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.forms.models import model_to_dict

from datetime import datetime, date

from .recommendation import Recommendation

from contracts.models import Contract, EnergyBill

from utils.energy_bill_util import EnergyBillUtils
from utils.subgroup_util import Subgroup


class University(models.Model):
    name = models.CharField(
        max_length=100,
        blank=False,
        null=False,
        unique=True,
        verbose_name=_('Nome'),
        help_text=_('Nome da universidade por extenso')
    )

    acronym = models.CharField(
        null=True,
        max_length=50,
        unique=True,
        verbose_name=_('Sigla'),
        help_text=_('Exemplo: UnB, UFSC, UFB')
    )

    cnpj = models.CharField(
        max_length=14,
        blank=False,
        null=False,
        unique=True,
        verbose_name=_('CNPJ'),
        help_text=_('14 números sem caracteres especiais')
    )

    is_active = models.BooleanField(
        default=True
    )

    created_on = models.DateField(
        auto_now_add=True
    )


class ConsumerUnit(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_('Nome'),
        help_text=_('Nome da Unidade Consumidora. Ex: Darcy Ribeiro')
    )

    code = models.CharField(
        max_length=30,
        verbose_name=_('Código da Unidade Consumidora'),
        help_text=_(
            'Cheque a conta de luz para obter o código da Unidade Consumidora. Insira apenas números')
    )

    is_active = models.BooleanField(
        default=True
    )

    university = models.ForeignKey(
        University,
        blank=False,
        null=False,
        on_delete=models.PROTECT,
        verbose_name='Universidade',
        related_name='consumer_units',
        help_text=_(
            'Uma Unidade Consumidora deve estar ligada a uma Universidade')
    )

    total_installed_power = models.DecimalField(
        decimal_places=2,
        max_digits=7,
        null=True,
        blank=True, 
        help_text=_(
            'Potência total de geração de energia instalada em kw'
        )
    )

    created_on = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ['university', 'name', 'code']

    @property
    def current_contract(self) -> Contract:
        return self.contract_set.all().order_by('start_date').last()

    @property
    def oldest_contract(self) -> Contract:
        return self.contract_set.all().order_by('start_date').first()
    
    @property
    def previous_contract(self) -> Contract:
        if self.current_contract is None:
            return None
        
        return self.contract_set.filter(start_date__lt=self.current_contract.start_date).order_by('start_date').last()

    @property
    def date(self):
        return self.oldest_contract.start_date

    @property
    def is_current_energy_bill_filled(self):
        if EnergyBill.get_energy_bill(
                self.id,
                date.today().month,
                date.today().year):

            return True
        return False

    @property
    def pending_energy_bills_number(self):
        return len(self.get_energy_bills_pending())

    @classmethod
    def check_insert_is_favorite_on_consumer_units(cls, consumer_unit_list, user_id):
        from users.models import UniversityUser

        updated_consumer_unit_list = []
        university_user: UniversityUser = UniversityUser.objects.get(
            id=user_id)

        for unit in consumer_unit_list:
            unit_dict = dict(unit)
            unit_dict['is_favorite'] = university_user.check_if_consumer_unit_is_your_favorite(
                unit_dict['id'])

            updated_consumer_unit_list.append(unit_dict)

        return updated_consumer_unit_list

    @classmethod
    def create_consumer_unit_and_contract(cls, data_consumer_unit, data_contract):
        created_consumer_unit = None

        try:
            Contract.check_is_valid_peak_demand_values(data_contract['peak_contracted_demand_in_kw'], data_contract['off_peak_contracted_demand_in_kw'])
            
            created_consumer_unit = ConsumerUnit(
                university_id=data_consumer_unit['university'],
                name=data_consumer_unit['name'],
                code=data_consumer_unit['code'],
                is_active=data_consumer_unit['is_active'],
                total_installed_power=data_consumer_unit["total_installed_power"]
            )

            created_contract = Contract(
                consumer_unit=created_consumer_unit,
                distributor_id=data_contract['distributor'],
                start_date=data_contract['start_date'],
                tariff_flag=data_contract['tariff_flag'],
                peak_contracted_demand_in_kw=data_contract['peak_contracted_demand_in_kw'],
                off_peak_contracted_demand_in_kw=data_contract['off_peak_contracted_demand_in_kw'],
            )
        except Exception as error:
            raise Exception(
                'error create consumer unit and contract: ' + str(error))

        created_consumer_unit.save()
        created_contract.save()

        return created_consumer_unit, created_contract

    @classmethod
    def edit_consumer_unit_and_contract(cls, data_consumer_unit, data_contract):
        try:
            Contract.check_is_valid_peak_demand_values(data_contract['peak_contracted_demand_in_kw'], data_contract['off_peak_contracted_demand_in_kw'])

            consumer_unit = ConsumerUnit.objects.get(id=data_consumer_unit['consumer_unit_id'])

            if not consumer_unit:
                raise Exception('Consumer Unit not exist')
            
            consumer_unit.name = data_consumer_unit['name']
            consumer_unit.code = data_consumer_unit['code']
            consumer_unit.is_active = data_consumer_unit['is_active']
            consumer_unit.total_installed_power = data_consumer_unit['total_installed_power']

            consumer_unit.save()
 
            contract = Contract.objects.get(id=data_contract['contract_id'])

            if not contract:
                raise Exception('Contract not exist')
            
            contract.distributor_id = data_contract['distributor']
            contract.start_date = datetime.strptime(data_contract['start_date'], '%Y-%m-%d').date()
            contract.tariff_flag = data_contract['tariff_flag']
            contract.subgroup = data_contract['subgroup']
            contract.peak_contracted_demand_in_kw = data_contract['peak_contracted_demand_in_kw']
            contract.off_peak_contracted_demand_in_kw = data_contract['off_peak_contracted_demand_in_kw']

            contract.check_start_date_edit_contract()
            contract.check_tariff_flag_is_valid()

            contract.save()
            
        except Exception as error:
            raise Exception(
                'error edit consumer unit and contract: ' + str(error))

        return consumer_unit, contract

    @classmethod
    def edit_consumer_unit_code_and_create_contract(cls, data_consumer_unit, data_contract):
        try:
            Contract.check_is_valid_peak_demand_values(data_contract['peak_contracted_demand_in_kw'], data_contract['off_peak_contracted_demand_in_kw'])
            
            consumer_unit = ConsumerUnit.objects.filter(id=data_consumer_unit['consumer_unit_id']).update(
                code=data_consumer_unit['code'],
            )

            created_contract = Contract(
                consumer_unit=consumer_unit.first(),
                distributor_id=data_contract['distributor'],
                start_date=data_contract['start_date'],
                tariff_flag=data_contract['tariff_flag'],
                subgroup=data_contract['subgroup'],
                peak_contracted_demand_in_kw=data_contract['peak_contracted_demand_in_kw'],
                off_peak_contracted_demand_in_kw=data_contract['off_peak_contracted_demand_in_kw'],
            )
        except Exception as error:
            raise Exception(
                'error create consumer unit and contract: ' + str(error))

        created_contract.save()

        return consumer_unit, created_contract
    
    def check_if_consumer_unit_has_contract(self):
        try:
            contract = self.current_contract
        except Exception:
            raise Exception('Unidade Consumidora sem Contrato ou Contrato com erro')

    def get_energy_bills_by_year(self, year):
        if year < self.date.year or year > date.today().year:
            raise Exception('Consumer User do not have Energy Bills this year')

        energy_bills_dates = EnergyBillUtils.generate_dates_by_year(year)

        for object in energy_bills_dates:
            object['energy_bill'] = None

            energy_bill = EnergyBill.get_energy_bill(
                self.id,
                object['month'],
                object['year'])

            if energy_bill:
                object['energy_bill'] = EnergyBillUtils.energy_bill_dictionary(
                    energy_bill)

        return list(energy_bills_dates)

    def get_energy_bills_pending(self):
        energy_bills_pending = []

        energy_bills = self.get_energy_bills_for_recommendation()

        for energy_bill in energy_bills:
            energy_bill_date = date(energy_bill['year'], energy_bill['month'], 1)

            if energy_bill_date >= self.oldest_contract.start_date:
                if energy_bill['energy_bill'] == None:
                    energy_bills_pending.append(energy_bill)

        return list(energy_bills_pending)

    def get_energy_bills_for_recommendation(self):
        return Recommendation.get_energy_bills_for_recommendation(self.id)

    def get_all_energy_bills(self):
        energy_bills = Recommendation.get_all_energy_bills_by_consumer_unit(
            self.id, self.date)

        return energy_bills

    def __repr__(self) -> str:
        return f'UC {self.name}'
