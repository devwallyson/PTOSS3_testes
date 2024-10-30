from rest_framework import serializers

from universities.models import ConsumerUnit, Contract
from tariffs.models import Distributor
from contracts.validators import CsvFileValidator
from . import models

class ContractSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    subgroup = serializers.CharField()
    end_date = serializers.DateField(read_only=True)

    consumer_unit = serializers.PrimaryKeyRelatedField(
        queryset=ConsumerUnit.objects.all())
    distributor = serializers.PrimaryKeyRelatedField(
        queryset=Distributor.objects.all())

    class Meta:
        model = models.Contract
        fields = fields = ['url', 'id', 'consumer_unit', 'distributor', 'start_date', 'end_date', 'tariff_flag',
                           'subgroup', 'peak_contracted_demand_in_kw', 'off_peak_contracted_demand_in_kw']


class ContractListSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    subgroup = serializers.CharField(read_only=True)
    end_date = serializers.DateField(read_only=True)

    consumer_unit = serializers.PrimaryKeyRelatedField(
        queryset=ConsumerUnit.objects.all())
    distributor = serializers.PrimaryKeyRelatedField(
        queryset=Distributor.objects.all())
    distributor_name = serializers.CharField(source='get_distributor_name')

    class Meta:
        model = models.Contract
        fields = fields = ['url', 'id', 'consumer_unit', 'distributor', 'distributor_name', 'start_date', 'end_date', 'tariff_flag',
                           'subgroup', 'peak_contracted_demand_in_kw', 'off_peak_contracted_demand_in_kw']


class EnergyBillSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)

    contract = serializers.PrimaryKeyRelatedField(
        queryset=Contract.objects.all())
    consumer_unit = serializers.PrimaryKeyRelatedField(
        queryset=ConsumerUnit.objects.all())

    class Meta:
        model = models.EnergyBill
        fields = '__all__'


class ContractListParamsSerializer(serializers.Serializer):
    consumer_unit_id = serializers.IntegerField()


class EnergyBillListParamsSerializer(serializers.Serializer):
    consumer_unit_id = serializers.IntegerField()


class SubgroupSerializerForDocs(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    min = serializers.CharField(read_only=True)
    max = serializers.CharField(read_only=True)


class ListSubgroupsSerializerForDocs(serializers.Serializer):
    subgroups = SubgroupSerializerForDocs(many=True, read_only=True)


class EnergyBillListObjectAttributesSerializerForDocs(serializers.Serializer):
    id = serializers.IntegerField()
    date = serializers.DateField()
    invoice_in_reais = serializers.DecimalField(decimal_places=2, max_digits=10)
    is_atypical = serializers.BooleanField()
    peak_consumption_in_kwh = serializers.DecimalField(decimal_places=2, max_digits=9)
    off_peak_consumption_in_kwh = serializers.DecimalField(decimal_places=2, max_digits=9)
    off_peak_contracted_demand_in_kw = serializers.DecimalField(decimal_places=2, max_digits=10)
    peak_measured_demand_in_kw = serializers.DecimalField(decimal_places=2, max_digits=9)
    off_peak_measured_demand_in_kw = serializers.DecimalField(decimal_places=2, max_digits=9)
    energy_bill_file = serializers.FileField()


class EnergyBillListObjectSerializerForDocs(serializers.Serializer):
    month = serializers.IntegerField()
    year = serializers.IntegerField()
    is_energy_bill_pending = serializers.BooleanField()
    energy_bill = EnergyBillListObjectAttributesSerializerForDocs()


class EnergyBillListSerializerForDocs(serializers.Serializer):
    year = EnergyBillListObjectSerializerForDocs(many=True, read_only=True)


class CSVFileSerializer(serializers.Serializer):
    file = serializers.FileField()
    consumer_unit_id = serializers.IntegerField()

    def validate_file(self, file):
        validator = CsvFileValidator()
        df = validator(file)
        return df
