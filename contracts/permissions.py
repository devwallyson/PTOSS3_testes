from rest_framework import permissions


class ContractPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous or request.user.is_admin:
            return False

        if request.user.university is None:
            return False

        if request.user.is_guest:
            return request.method in permissions.SAFE_METHODS

        return True

    def has_object_permission(self, request, view, obj):
        return obj.consumer_unit.university == request.user.university
