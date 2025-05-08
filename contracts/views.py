import logging
import os

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from contracts.models import Contract, EnergyBill
from contracts.permissions import ContractPermission
from universities.models import ConsumerUnit
from utils.mixins.cache_mixin import CacheModelMixin, ReadOnlyCacheMixin
from utils.subgroup_util import Subgroup

from . import serializers, services


class ContractViewSet(ReadOnlyCacheMixin, ReadOnlyModelViewSet):
    queryset = Contract.objects.all()
    serializer_class = serializers.ContractSerializer
    cache_key_prefix = "contract_viewset"
    cache_timeout = 3600 * 6
    permission_classes = [ContractPermission]

    def get_queryset(self):
        return Contract.objects.filter(consumer_unit__university=self.request.user.university)

    @method_decorator(cache_page(cache_timeout, key_prefix=cache_key_prefix))
    def list(self, request: Request, *args, **kwargs):
        request_consumer_unit_id = request.GET.get("consumer_unit_id")
        queryset = self.get_queryset()
        if request_consumer_unit_id:
            consumer_unit = get_object_or_404(ConsumerUnit, id=request_consumer_unit_id)
            university_id = consumer_unit.university.id
            if self.request.user.university.id != university_id:
                raise PermissionDenied()
            queryset = Contract.objects.filter(consumer_unit=consumer_unit.id)
        serializer = serializers.ContractSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data, status.HTTP_200_OK)

    @method_decorator(cache_page(cache_timeout, key_prefix=cache_key_prefix))
    def retrieve(self, request, pk=None):
        contract = self.get_object()
        university_id = contract.consumer_unit.university.id
        if contract.consumer_unit.university != request.user.university:
            raise PermissionDenied()
        serializer = self.get_serializer(contract)
        return Response(serializer.data)

    @swagger_auto_schema(responses={200: serializers.ListSubgroupsSerializerForDocs(many=True)})
    @method_decorator(cache_page(cache_timeout, key_prefix=cache_key_prefix))
    @action(detail=False, methods=["get"], url_path="list-subgroups")
    def list_subgroups(self, request: Request, pk=None):
        try:
            subgroups = {"subgroups": Subgroup.get_all_subgroups()}
        except Exception as error:
            return Response({"list subgroups error": f"{error}"}, status.HTTP_400_BAD_REQUEST)

        return JsonResponse(subgroups, safe=False)

    @swagger_auto_schema(
        query_serializer=serializers.ContractListSerializer, responses={200: serializers.ContractListSerializer}
    )
    @method_decorator(cache_page(cache_timeout, key_prefix=cache_key_prefix))
    @action(detail=False, methods=["get"], url_path="get-current-contract-of-consumer-unit")
    def get_current_contract_of_consumer_unit(self, request: Request, pk=None):
        request_consumer_unit_id = request.GET.get("consumer_unit_id")

        consumer_unit = get_object_or_404(ConsumerUnit, id=request_consumer_unit_id)
        if consumer_unit.university != request.user.university:
            raise PermissionDenied()

        contract = consumer_unit.current_contract
        serializer = serializers.ContractListSerializer(contract, many=False, context={"request": request})
        return Response(serializer.data, status.HTTP_200_OK)


class EnergyBillViewSet(CacheModelMixin, ModelViewSet):
    queryset = EnergyBill.objects.all()
    serializer_class = serializers.EnergyBillSerializer
    cache_key_prefix = "energybill_viewset"
    cache_timeout = 3600 * 168  # 3600 segundos * 24  = 1 dia (dados nao mudam com frequência)
    permission_classes = [ContractPermission]

    def get_queryset(self):
        return EnergyBill.objects.filter(consumer_unit__university=self.request.user.university)

    def retrieve(self, request, pk=None):
        energy_bill = self.get_object()
        if energy_bill.consumer_unit.university != self.request.user.university:
            raise PermissionDenied()
        serializer = self.get_serializer(energy_bill)
        return Response(serializer.data)

    def perform_update(self, serializer):
        energy_bill = self.get_object()
        serializer.validated_data["consumer_unit"] = energy_bill.consumer_unit
        serializer.validated_data["contract"] = energy_bill.contract
        super().perform_update(serializer)
        self.delete_view_cache()

    def create(self, request, *args, **kwargs):
        consumer_unit = get_object_or_404(ConsumerUnit, id=self.request.data.get("consumer_unit"))
        contract = get_object_or_404(Contract, id=self.request.data.get("contract"))

        if consumer_unit.university != self.request.user.university:
            raise PermissionDenied()
        if contract.consumer_unit.id != consumer_unit.id:
            raise PermissionDenied()

        try:
            response = super().create(request, *args, **kwargs)
            self.delete_view_cache()
            return response
        except Exception as error:
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)

    def perform_destroy(self, instance):
        if self.request.user.university != instance.consumer_unit.university:
            raise PermissionDenied()
        super().perform_destroy(instance)
        self.delete_view_cache()

    @swagger_auto_schema(
        responses={200: serializers.EnergyBillListSerializerForDocs(many=True)},
    )
    @method_decorator(cache_page(cache_timeout, key_prefix=cache_key_prefix))
    def list(self, request: Request, *args, **kwargs):
        request_consumer_unit_id = request.GET.get("consumer_unit_id")

        consumer_unit = get_object_or_404(ConsumerUnit, id=request_consumer_unit_id)
        if consumer_unit.university != request.user.university:
            raise PermissionDenied()

        if request_consumer_unit_id:
            energy_bills = consumer_unit.get_all_energy_bills()
            return Response(energy_bills)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="multiple_create")
    def multiple_create(self, request, *args, **kwargs):
        consumer_unit_id = request.data.get("consumer_unit")
        contract_id = request.data.get("contract")
        energy_bills_data = request.data.get("energy_bills", [])
        response_data = []
        errors = []

        consumer_unit = get_object_or_404(ConsumerUnit, id=consumer_unit_id)
        contract = get_object_or_404(Contract, id=contract_id)
        if consumer_unit.university != request.user.university:
            raise PermissionDenied()
        if contract.consumer_unit.id != consumer_unit.id:
            raise PermissionDenied()

        def round_value(value):
            if isinstance(value, int | float | Decimal):
                return str(Decimal(value).quantize(Decimal("1.00"), rounding=ROUND_HALF_UP))
            return value

        for bill_data in energy_bills_data:
            date_str = bill_data.get("date")

            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                errors.append({"error": "Invalid date format", "data": bill_data})
                continue

            if EnergyBill.check_energy_bill_month_year(consumer_unit_id, date):
                errors.append(
                    {
                        "error": "There is already an energy bill this month and year for this consumer unit",
                        "data": bill_data,
                    }
                )
                continue

            if not EnergyBill.check_energy_bill_covered_by_contract(consumer_unit_id, date):
                errors.append({"error": "No contract covers the date of this energy bill", "data": bill_data})
                continue

            bill_data["consumer_unit"] = consumer_unit_id
            bill_data["contract"] = contract_id

            bill_data = {key: round_value(value) for key, value in bill_data.items()}

            serializer = self.get_serializer(data=bill_data)
            if not serializer.is_valid():
                errors.append({"error": "Validation error", "data": bill_data, "details": serializer.errors})

        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        for bill_data in energy_bills_data:
            bill_data["consumer_unit"] = consumer_unit_id
            bill_data["contract"] = contract_id

            bill_data = {key: round_value(value) for key, value in bill_data.items()}

            serializer = self.get_serializer(data=bill_data)
            if serializer.is_valid():
                serializer.save()
                response_data.append(serializer.data)

        self.delete_related_view_cache(
            additional_viewsets=[
                "contracts.views.EnergyBillViewSet",
                "contracts.views.ContractViewSet",
                "universities.views.ConsumerUnitViewSet",
            ]
        )
        return Response({"created": response_data}, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(method="post")
    @action(detail=False, methods=["post"], url_path="upload")
    def upload_csv(self, request, *args, **kwargs):
        logger = logging.getLogger("uc_sheet")
        energy_bill_data = []
        serializer = serializers.CSVFileSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        consumer_unit_id = serializer.validated_data["consumer_unit_id"]

        consumer_unit = get_object_or_404(ConsumerUnit, id=consumer_unit_id)
        if consumer_unit.university != request.user.university:
            raise PermissionDenied()

        logger.info(f"Consumer unit with id: {consumer_unit_id} is uploading a file")
        energy_bill_data = services.ContractServices().get_file_errors(
            serializer.validated_data["file"], consumer_unit_id
        )
        return Response({"data": energy_bill_data}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="download-csv-model")
    def download_csv_model(self, request):
        file_path = os.path.join(settings.BASE_DIR, "docs", "modelo_importar_tarifas.csv")

        if os.path.exists(file_path):
            return FileResponse(open(file_path, "rb"), as_attachment=True, filename=os.path.basename(file_path))
        else:
            return Response("Document does not exist", status=400)

    @action(detail=False, methods=["get"], url_path="download-xlsx-model")
    def download_xlsx_model(self, request):
        file_path = os.path.join(settings.BASE_DIR, "docs", "modelo_importar_tarifas.xlsx")

        if os.path.exists(file_path):
            return FileResponse(open(file_path, "rb"), as_attachment=True, filename=os.path.basename(file_path))
        else:
            return Response("Document does not exist", status=400)

    @action(detail=False, methods=["get"], url_path="plot-graph", permission_classes=[])
    def plot_graph(self, request):
        consumer_unit_id = request.query_params.get("consumer_unit_id", None)
        if consumer_unit_id is None:
            return Response({"error": "consumer_unit_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        consumer_unit = get_object_or_404(ConsumerUnit, id=consumer_unit_id)
        if consumer_unit.university != request.user.university:
            raise PermissionDenied()

        current_month = date.today().replace(day=1) - relativedelta(months=1)
        months = int(request.query_params.get("months", 12))
        all_months = [current_month - relativedelta(months=i) for i in range(months - 1, -1, -1)]

        energy_bills_qs = (
            EnergyBill.objects.filter(
                consumer_unit=consumer_unit_id,
                date__gte=all_months[0],
                date__lte=all_months[-1],
            )
            .values(
                "date",
                "peak_consumption_in_kwh",
                "off_peak_consumption_in_kwh",
                "peak_measured_demand_in_kw",
                "off_peak_measured_demand_in_kw",
            )
            .order_by("date")
        )

        if not energy_bills_qs.exists():
            return Response(
                {"errors": ["No energy bills found for this consumer unit in the time period"]},
                status=status.HTTP_404_NOT_FOUND,
            )

        bills_by_month = {bill["date"].strftime("%Y-%m"): bill for bill in energy_bills_qs}

        energy_bills = []
        for month in all_months:
            year_month = month.strftime("%Y-%m")
            bill = bills_by_month.get(year_month, {})
            bill_data = {
                "date": month.strftime("%Y-%m-%d"),
                "peak_consumption_in_kwh": bill.get("peak_consumption_in_kwh"),
                "off_peak_consumption_in_kwh": bill.get("off_peak_consumption_in_kwh"),
                "peak_measured_demand_in_kw": bill.get("peak_measured_demand_in_kw"),
                "off_peak_measured_demand_in_kw": bill.get("off_peak_measured_demand_in_kw"),
            }
            energy_bills.append(bill_data)

        graph_data = {"energy_bills": energy_bills, "contract_data": consumer_unit.current_contract}
        serializer = serializers.EnergyBillGraphSerializer(graph_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
