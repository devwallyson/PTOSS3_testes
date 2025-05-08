import os

from django.conf import settings
from django.http import FileResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from universities.models import ConsumerUnit
from universities.serializers import ConsumerUnitSerializer
from utils.mixins.cache_mixin import ReadOnlyCacheMixin
from utils.tariff_util import response_tariffs_of_distributor

from .models import Distributor, Tariff
from .serializers import (
    ConsumerUnitsSeparatedBySubgroupSerializerForDocs,
    DistributorSerializer,
    GetTariffsOfDistributorForDocs,
    GetTariffsOfDistributorParamsSerializer,
    TariffSerializer,
)


class DistributorViewSet(ReadOnlyCacheMixin, ReadOnlyModelViewSet):
    queryset = Distributor.objects.all()
    serializer_class = DistributorSerializer
    cache_key_prefix = "distributor_viewset"
    cache_timeout = 3600 * 24

    @action(detail=True, methods=["get"], url_path="consumer-units")
    def consumer_units(self, request: Request, pk=None):
        distributor = self.get_object()
        university = request.user.university
        if not university:
            raise PermissionDenied("User does not have a university associated with them.")

        consumer_units = ConsumerUnit.objects.filter(
            contract__end_date__isnull=True,
            contract__distributor=distributor,
            university=university,
        )
        serializer = ConsumerUnitSerializer(consumer_units, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={200: ConsumerUnitsSeparatedBySubgroupSerializerForDocs()})
    @method_decorator(cache_page(cache_timeout, key_prefix=cache_key_prefix))
    @action(detail=True, methods=["get"], url_path="consumer-units-by-subgroup")
    def consumer_units_separated_by_subgroup(self, request: Request, pk=None):
        distributor: Distributor = self.get_object()
        university = request.user.university
        if not university:
            raise PermissionDenied("User does not have a university associated with them.")

        consumer_units = distributor.get_consumer_units_separated_by_subgroup(university)
        return Response(consumer_units, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses={200: GetTariffsOfDistributorForDocs()}, query_serializer=GetTariffsOfDistributorParamsSerializer
    )
    @method_decorator(cache_page(cache_timeout, key_prefix=cache_key_prefix))
    @action(detail=True, methods=["get"], url_path="get-tariffs")
    def get_blue_and_green_tariffs(self, request: Request, pk=None):
        distributor: Distributor = self.get_object()

        params_serializer = GetTariffsOfDistributorParamsSerializer(data=request.GET)
        if not params_serializer.is_valid():
            return Response(params_serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        request_subgroup = request.GET.get("subgroup")
        blue_tariff, green_tariff = distributor.get_tariffs_by_subgroups(request_subgroup)

        response = response_tariffs_of_distributor(
            blue_tariff.start_date if blue_tariff else None,
            blue_tariff.end_date if blue_tariff else None,
            blue_tariff.pending if blue_tariff else True,
            blue_tariff,
            green_tariff,
        )
        return Response(response, status.HTTP_200_OK)


class TariffViewSet(ReadOnlyCacheMixin, ReadOnlyModelViewSet):
    queryset = Tariff.objects.all()
    serializer_class = TariffSerializer
    cache_key_prefix = "tariff_viewset"
    cache_timeout = 3600 * 24


class DownloadPDFViewSet(ViewSet):
    def list(self, request):
        file_path = os.path.join(settings.BASE_DIR, "docs", "Pegar_tarifas_da_distribuidora_2023.pdf")

        if os.path.exists(file_path):
            return FileResponse(open(file_path, "rb"), as_attachment=True, filename=os.path.basename(file_path))
        else:
            return Response("Document does not exist", status=400)
