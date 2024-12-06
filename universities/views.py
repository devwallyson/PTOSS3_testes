from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from universities import serializers
from universities.models import ConsumerUnit, University
from universities.serializers import (
    ConsumerUnitWithContractSerializer,
)
from users.models import CustomUser, UniversityUser
from users.requests_permissions import RequestsPermissions
from utils.mixins.cache_mixin import CachedViewSetMixin


class UniversityViewSet(CachedViewSetMixin, ModelViewSet):
    queryset = University.objects.all()
    serializer_class = serializers.UniversitySerializer
    http_method_names = ["post", "put", "get"]
    cache_key_prefix = "university_viewset"
    cache_timeout = 3600 * 168

    def create(self, request, *args, **kwargs):
        user_types_with_permission = RequestsPermissions.super_user_permissions

        try:
            RequestsPermissions.check_request_permissions(request.user, user_types_with_permission, None)
        except Exception as error:
            return Response({"detail": f"{error}"}, status.HTTP_401_UNAUTHORIZED)

        self.delete_view_cache()
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        user_types_with_permission = RequestsPermissions.super_user_permissions
        university = self.get_object()

        try:
            RequestsPermissions.check_request_permissions(request.user, user_types_with_permission, university.id)
        except Exception as error:
            return Response({"detail": f"{error}"}, status.HTTP_401_UNAUTHORIZED)

        self.delete_view_cache()
        return super().update(request, *args, **kwargs)

    @method_decorator(cache_page(cache_timeout, key_prefix=cache_key_prefix))
    def list(self, request, *args, **kwargs):
        user_types_with_permission = RequestsPermissions.super_user_permissions

        try:
            RequestsPermissions.check_request_permissions(request.user, user_types_with_permission, None)
        except Exception as error:
            return Response({"detail": f"{error}"}, status.HTTP_401_UNAUTHORIZED)

        queryset = University.objects.all()
        serializer = serializers.UniversitySerializer(queryset, many=True, context={"request": request})

        return Response(serializer.data, status.HTTP_200_OK)

    @method_decorator(cache_page(cache_timeout, key_prefix=cache_key_prefix))
    def retrieve(self, request, *args, **kwargs):
        user_types_with_permission = RequestsPermissions.default_users_permissions
        university = self.get_object()

        try:
            RequestsPermissions.check_request_permissions(request.user, user_types_with_permission, university.id)
        except Exception as error:
            return Response({"detail": f"{error}"}, status.HTTP_401_UNAUTHORIZED)

        serializer = self.get_serializer(university)
        return Response(serializer.data)


class ConsumerUnitViewSet(CachedViewSetMixin, ModelViewSet):
    queryset = ConsumerUnit.objects.all()
    serializer_class = serializers.ConsumerUnitSerializer
    http_method_names = ["get", "post", "put"]
    cache_key_prefix = "consumer_units_viewset"
    cache_timeout = 3600 * 168

    def create(self, request, *args, **kwargs):
        user_types_with_permission = RequestsPermissions.university_user_permissions

        body_university_id = request.data["university"]

        try:
            RequestsPermissions.check_request_permissions(request.user, user_types_with_permission, body_university_id)
        except Exception as error:
            return Response({"detail": f"{error}"}, status.HTTP_401_UNAUTHORIZED)

        self.delete_view_cache()
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        user_types_with_permission = RequestsPermissions.university_user_permissions
        consumer_unit = self.get_object()

        try:
            RequestsPermissions.check_request_permissions(
                request.user, user_types_with_permission, consumer_unit.university.id
            )
        except Exception as error:
            return Response({"detail": f"{error}"}, status.HTTP_401_UNAUTHORIZED)

        self.delete_view_cache()
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        query_serializer=serializers.ConsumerUnitParamsSerializer,
        responses={200: serializers.ListConsumerUnitSerializerForDocs},
    )
    @method_decorator(cache_page(cache_timeout, key_prefix=cache_key_prefix))
    def list(self, request: Request, *args, **kwargs):
        user_types_with_permission = RequestsPermissions.default_users_permissions

        params_serializer = serializers.ConsumerUnitParamsSerializer(data=request.GET)
        if not params_serializer.is_valid():
            return Response(params_serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        request_university_id = request.GET.get("university_id")

        try:
            RequestsPermissions.check_request_permissions(
                request.user, user_types_with_permission, request_university_id
            )
        except Exception as error:
            return Response({"detail": f"{error}"}, status.HTTP_401_UNAUTHORIZED)

        queryset = ConsumerUnit.objects.filter(university=request_university_id)
        serializer = serializers.ConsumerUnitSerializer(queryset, many=True, context={"request": request})

        consumer_units = serializer.data

        try:
            # Buscando se as Unidades Consumidoras estão na lista de favoritas do Usuário Universidade
            if request.user.type in CustomUser.university_user_types:
                consumer_units = ConsumerUnit.check_insert_is_favorite_on_consumer_units(
                    consumer_units, request.user.id
                )
        except Exception as error:
            return Response(
                {"detail": f"Error in searching if the consumer unit is the user`s favorite - {error}"},
                status.HTTP_400_BAD_REQUEST,
            )

        consumer_units = sorted(consumer_units, key=lambda x: (not x["is_active"], not x["is_favorite"], x["name"]))

        return Response(consumer_units, status.HTTP_200_OK)

    @method_decorator(cache_page(cache_timeout, key_prefix=cache_key_prefix))
    def retrieve(self, request, *args, pk=None, **kwargs):
        user_types_with_permission = RequestsPermissions.default_users_permissions
        queryset = self.get_object()
        university_user: UniversityUser = UniversityUser.objects.get(id=request.user.id)

        try:
            RequestsPermissions.check_request_permissions(
                request.user, user_types_with_permission, queryset.university.id
            )
        except Exception as error:
            return Response({"detail": f"{error}"}, status.HTTP_401_UNAUTHORIZED)

        serializer = self.get_serializer(queryset)
        consumer_unit = serializer.data

        try:
            if request.user.type in CustomUser.university_user_types:
                consumer_unit["is_favorite"] = university_user.check_if_consumer_unit_is_your_favorite(pk)
        except Exception as error:
            return Response(
                {"detail": f"Error in searching if the consumer unit is the user`s favorite - {error}"},
                status.HTTP_400_BAD_REQUEST,
            )

        return Response(consumer_unit, status.HTTP_200_OK)

    @swagger_auto_schema(request_body=ConsumerUnitWithContractSerializer)
    @action(detail=False, methods=["post"])
    def create_consumer_unit_and_contract(self, request):
        try:
            user_types_with_permission = RequestsPermissions.university_user_permissions
            body_university_id = request.data["consumer_unit"]["university"]
            RequestsPermissions.check_request_permissions(request.user, user_types_with_permission, body_university_id)
        except Exception as error:
            return Response({"detail": f"{error}"}, status.HTTP_401_UNAUTHORIZED)

        serializer = ConsumerUnitWithContractSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.delete_related_view_cache(
            additional_viewsets=[
                "contracts.views.ContractViewSet",
                "universities.views.ConsumerUnitViewSet",
            ]
        )
        return Response(serializer.data, status.HTTP_201_CREATED)

    @swagger_auto_schema(request_body=ConsumerUnitWithContractSerializer)
    @action(detail=True, methods=["put"])
    def edit_consumer_unit_and_contract(self, request, pk=None):
        try:
            user_types_with_permission = RequestsPermissions.university_user_permissions
            body_university_id = request.data["consumer_unit"]["university"]
            RequestsPermissions.check_request_permissions(request.user, user_types_with_permission, body_university_id)
        except Exception as error:
            return Response({"detail": f"{error}"}, status.HTTP_401_UNAUTHORIZED)

        consumer_unit_instance = self.get_object()
        serializer = ConsumerUnitWithContractSerializer(consumer_unit_instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.delete_related_view_cache(
            additional_viewsets=[
                "contracts.views.ContractViewSet",
                "universities.views.ConsumerUnitViewSet",
            ]
        )

        return Response(serializer.data, status.HTTP_201_CREATED)
