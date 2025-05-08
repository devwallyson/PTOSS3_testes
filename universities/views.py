from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from tariffs.serializers import DistributorSerializer
from universities.models import ConsumerUnit, University
from universities.permissions import ConsumerUnitPermission, UniversityPermission
from universities.serializers import (
    ConsumerUnitSerializer,
    ConsumerUnitWithContractSerializer,
    UniversityDistributorSerializer,
    UniversitySerializer,
)
from utils.mixins.cache_mixin import CacheModelMixin, ReadOnlyCacheMixin


class UniversityViewSet(CacheModelMixin, ModelViewSet):
    queryset = University.objects.all()
    serializer_class = UniversitySerializer
    permission_classes = [UniversityPermission]
    cache_key_prefix = "university_viewset"
    cache_timeout = 3600 * 168

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return University.objects.all()
        return University.objects.filter(id=user.university.id)

    def get_serializer_class(self):
        if self.action == "get_distributors":
            return DistributorSerializer
        if self.action in ["set_distributors"]:
            return UniversityDistributorSerializer
        return super().get_serializer_class()

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed("DELETE", "You cannot delete a university.")

    @action(detail=True, methods=["get"], url_path="distributors")
    def get_distributors(self, request, pk=None):
        university = self.get_object()
        distributors = university.distributors.all()

        is_pending = request.query_params.get("is_pending", None)
        if is_pending in ["true", "True", "1", "yes"]:
            # Corrigir a lógica para filtrar distribuidoras pendentes
            distributors = [d for d in distributors if d.is_pending]

        distributors = distributors.order_by("name")
        serializer = self.get_serializer(distributors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="set-distributors")
    def set_distributors(self, request, pk=None):
        university = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        distributors = serializer.validated_data.get("distributors", [])
        university.distributors.set(distributors)
        distributors_names = [distributor.name for distributor in distributors]
        return Response({"detail": f"Distributors set successfully: {distributors_names}."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="clear-distributors")
    def clear_distributors(self, request, pk=None):
        university = self.get_object()
        university.distributors.clear()
        university.save()
        return Response({"detail": "All distributors cleared successfully."}, status=status.HTTP_200_OK)


class ConsumerUnitViewSet(ReadOnlyCacheMixin, ReadOnlyModelViewSet):
    queryset = ConsumerUnit.objects.all()
    serializer_class = ConsumerUnitSerializer
    permission_classes = [ConsumerUnitPermission]
    cache_key_prefix = "consumer_units_viewset"
    cache_timeout = 3600 * 168

    def get_queryset(self):
        return ConsumerUnit.objects.filter(university=self.request.user.university)

    def perform_create(self, serializer):
        serializer.save(university=self.request.user.university)
        self.delete_related_view_cache()

    @method_decorator(cache_page(cache_timeout, key_prefix=cache_key_prefix))
    def list(self, request: Request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        consumer_units = ConsumerUnit.check_insert_is_favorite_on_consumer_units(serializer.data, request.user.id)
        consumer_units = sorted(consumer_units, key=lambda x: (not x["is_active"], not x["is_favorite"], x["name"]))
        return Response(consumer_units, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=ConsumerUnitWithContractSerializer)
    @action(detail=False, methods=["post"])
    def create_consumer_unit_and_contract(self, request):
        request_data = request.data.copy()
        request_data["consumer_unit"]["university"] = request.user.university.id
        serializer = ConsumerUnitWithContractSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.delete_related_view_cache(
            additional_viewsets=[
                "contracts.views.ContractViewSet",
                "universities.views.ConsumerUnitViewSet",
            ]
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(request_body=ConsumerUnitWithContractSerializer)
    @action(detail=True, methods=["put"])
    def edit_consumer_unit_and_contract(self, request, pk=None):
        request_data = request.data.copy()
        consumer_unit_instance = self.get_object()
        request_data["consumer_unit"]["university"] = consumer_unit_instance.university.id
        serializer = ConsumerUnitWithContractSerializer(consumer_unit_instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.delete_related_view_cache(
            additional_viewsets=[
                "contracts.views.ContractViewSet",
                "universities.views.ConsumerUnitViewSet",
            ]
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
