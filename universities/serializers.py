from decimal import Decimal

from rest_framework import serializers

from contracts.models import Contract
from utils.cnpj_validator_util import CnpjValidator

from .models import ConsumerUnit, University


class UniversitySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = University
        fields = [
            "url",
            "id",
            "name",
            "acronym",
            "cnpj",
            "is_active",
            "created_on",
        ]

    def validate_cnpj(self, cnpj: str):
        try:
            CnpjValidator.validate(cnpj)
        except Exception as e:
            raise serializers.ValidationError(str(e.args))
        return cnpj


class ConsumerUnitSerializer(serializers.HyperlinkedModelSerializer):
    name = serializers.CharField()
    code = serializers.CharField()
    is_active = serializers.BooleanField()
    university = serializers.PrimaryKeyRelatedField(queryset=University.objects.all())
    total_installed_power = serializers.DecimalField(
        max_digits=7,
        min_value=Decimal("0.00"),
        decimal_places=2,
        allow_null=True,
    )

    class Meta:
        model = ConsumerUnit
        fields = [
            "id",
            "url",
            "name",
            "code",
            "is_active",
            "date",
            "is_current_energy_bill_filled",
            "pending_energy_bills_number",
            "university",
            "total_installed_power",
            "created_on",
        ]


class ListConsumerUnitSerializerForDocs(ConsumerUnitSerializer):
    is_favorite = serializers.BooleanField()

    class Meta:
        model = ConsumerUnit
        fields = [
            "id",
            "url",
            "name",
            "code",
            "is_active",
            "date",
            "pending_energy_bills_number",
            "university",
            "created_on",
            "is_current_energy_bill_filled",
            "is_favorite",
        ]


class ConsumerUnitParamsSerializer(serializers.Serializer):
    university_id = serializers.IntegerField()


class UniversityUserAuthenticatedSerializerForDocs(serializers.ModelSerializer):
    name = serializers.CharField()
    code = serializers.CharField()
    is_active = serializers.BooleanField()


class CreateContractSerializerForDocs(serializers.ModelSerializer):
    start_date = serializers.DateField()
    tariff_flag = serializers.CharField()
    peak_contracted_demand_in_kw = serializers.DecimalField(decimal_places=2, max_digits=10)
    off_peak_contracted_demand_in_kw = serializers.DecimalField(decimal_places=2, max_digits=10)

    class Meta:
        model = Contract
        exclude = (
            "consumer_unit",
            "end_date",
            "subgroup",
        )


class EditConsumerUnitCodeSerializerForDocs(serializers.Serializer):
    consumer_unit_id = serializers.IntegerField()
    code = serializers.CharField()


class CreateConsumerUnitAndContractSerializerForDocs(serializers.Serializer):
    consumer_unit = ConsumerUnitSerializer()
    contract = CreateContractSerializerForDocs()


class EditConsumerUnitAndContractSerializerForDocs(serializers.Serializer):
    consumer_unit = ConsumerUnitSerializer()
    contract = CreateContractSerializerForDocs()


class EditConsumerUnitCodeAndCreateContractSerializerForDocs(serializers.Serializer):
    consumer_unit = EditConsumerUnitCodeSerializerForDocs()
    contract = CreateContractSerializerForDocs()
