from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from universities.models import ConsumerUnit

from .models import CustomUser, UniversityUser
from .permissions import UniversityUserPermission
from .requests_permissions import RequestsPermissions
from .serializers import (
    ChangeUniversityUserTypeSerializer,
    CustomUserSerializer,
    FavoriteConsumerUnitActionSerializer,
    ListUsersParamsSerializer,
    RetrieveUniversityUserSerializer,
    UniversityUserSerializer,
)


class CustomUserViewSet(ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    def create(self, request, *args, **kwargs):
        user_types_with_permission = RequestsPermissions.super_user_permissions

        try:
            RequestsPermissions.check_request_permissions(request.user, user_types_with_permission, None)
        except Exception as error:
            return Response({"detail": f"{error}"}, status.HTTP_401_UNAUTHORIZED)

    def update(self, request, *args, **kwargs):
        user_types_with_permission = {
            *RequestsPermissions.super_user_permissions,
            *RequestsPermissions.admin_permission,
        }

        if request.user.type not in user_types_with_permission:
            return Response({"detail": "This User does not have permission."}, status=status.HTTP_401_UNAUTHORIZED)

        instance = self.get_object()
        new_user_type = request.data.get("type")

        if request.user.universityuser.university != instance.universityuser.university:
            return Response(
                {"detail": "Admins can only edit users from their own university."}, status=status.HTTP_403_FORBIDDEN
            )

        if new_user_type in RequestsPermissions.super_user_permissions:
            forbidden_user_types = ["university_user"] + list(RequestsPermissions.admin_permission)
            if instance.type in forbidden_user_types:
                return Response({"detail": "Admins cannot promote to Super Users."}, status=status.HTTP_403_FORBIDDEN)

        return super().update(request, *args, **kwargs)

    @action(detail=False, methods=["post"], url_path="change-user-password")
    def change_user_password(self, request: Request, pk=None):
        user = request.user
        data = request.data

        current_password = data.get("current_password")
        new_password = data.get("new_password")

        if not current_password or not new_password:
            return Response({"error": "Todos os campos são obrigatórios"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(id=user.id)
            user.change_user_password(current_password, new_password)
        except CustomUser.DoesNotExist:
            return Response({"error": "Usuário não encontrado"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as error:
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Senha alterada com sucesso"}, status=status.HTTP_200_OK)

    @swagger_auto_schema(query_serializer=ListUsersParamsSerializer)
    def list(self, request):
        user_types_with_permission = RequestsPermissions.admin_permission

        try:
            request_university_id = (
                request.GET.get("university_id") if request.user.type != CustomUser.super_user_type else None
            )

            RequestsPermissions.check_request_permissions(
                request.user, user_types_with_permission, request_university_id
            )
        except Exception as error:
            return Response({"detail": f"{error}"}, status.HTTP_401_UNAUTHORIZED)

        if request.user.type == CustomUser.super_user_type:
            queryset = CustomUser.objects.all()
        else:
            queryset = UniversityUser.objects.filter(university=request_university_id)

        serializer = CustomUserSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data, status.HTTP_200_OK)


class UniversityUsersViewSet(ModelViewSet):
    queryset = UniversityUser.objects.all()
    serializer_class = UniversityUserSerializer
    permission_classes = [UniversityUserPermission]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return UniversityUser.objects.all()
        university_user = UniversityUser.objects.get(id=user.id)
        if user.is_manager:
            return UniversityUser.objects.filter(university=university_user.university)
        return UniversityUser.objects.filter(id=user.id)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        user = self.request.user
        if user.is_staff or user.is_admin:
            serializer.save()
            return

        university_id = UniversityUser.objects.filter(id=user.id).values_list("university", flat=True).first()
        user_type = serializer.validated_data.get("type")
        allowed_types = ["university_admin", "university_user"]

        if not user.is_manager:
            raise PermissionDenied("Common users cannot create accounts.")
        elif user_type not in allowed_types:
            raise PermissionDenied("Managers can only create 'university_admin' or 'university_user' accounts.")

        serializer.save(university_id=university_id)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, serializer):
        user = self.request.user
        if user.is_staff:
            serializer.delete()
        else:
            raise PermissionDenied("Only super_admin can delete an account.")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        user = self.request.user
        if user.is_staff:
            serializer.save()
            return
        university_user = UniversityUser.objects.get(id=user.id)
        user_type = serializer.validated_data.get("type")
        if user.is_manager:
            if user_type == "super_user":
                raise PermissionDenied("Managers cannot change type to 'super_user'.")
            serializer.save(university=university_user.university)
        else:
            serializer.save(university=university_user.university, type=university_user.type)

    def get_serializer_class(self):
        if self.request.method == "retrieve":
            return RetrieveUniversityUserSerializer
        return UniversityUserSerializer

    @swagger_auto_schema(request_body=FavoriteConsumerUnitActionSerializer)
    @action(detail=True, methods=["post"], url_path="favorite-consumer-units")
    def add_or_remove_favorite_consumer_unit(self, request: Request, pk=None):
        params_serializer = FavoriteConsumerUnitActionSerializer(data=request.data)
        if not params_serializer.is_valid():
            return Response(params_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user: UniversityUser = self.get_object()
        data = params_serializer.validated_data
        consumer_unit_id = data["consumer_unit_id"]
        action = data["action"]

        try:
            user.add_or_remove_favorite_consumer_unit(consumer_unit_id, action)
        except ConsumerUnit.DoesNotExist:
            return Response({"errors": ["Consumer unit not found"]}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"errors": e.args}, status=status.HTTP_403_FORBIDDEN)

        return Response(data, status.HTTP_200_OK)

    @swagger_auto_schema(request_body=ChangeUniversityUserTypeSerializer)
    @action(detail=False, methods=["post"], url_path="change-university-user-type")
    def change_university_user_type(self, request: Request, pk=None):
        user_types_with_permission = RequestsPermissions.admin_permission
        params_serializer = ChangeUniversityUserTypeSerializer(data=request.data)

        if not params_serializer.is_valid():
            return Response(params_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = request.data
        user_id = data["user_id"]
        new_user_type = data["new_user_type"]

        try:
            request_university_id = (
                UniversityUser.objects.get(id=request.user.id).university.id
                if request.user.type in CustomUser.university_user_types
                else None
            )

            RequestsPermissions.check_request_permissions(
                request.user, user_types_with_permission, request_university_id
            )
        except Exception as error:
            return Response({"detail": f"{error}"}, status.HTTP_401_UNAUTHORIZED)

        try:
            user_for_change = UniversityUser.objects.get(id=user_id)
            user_for_change.change_university_user_type(new_user_type)
        except Exception as error:
            return Response({"error": f"{error}"}, status.HTTP_400_BAD_REQUEST)

        return Response(data)
