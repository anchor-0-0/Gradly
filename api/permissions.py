from rest_framework import permissions


class IsDean(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Dean').exists()


class IsHOD(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='HOD').exists()


class IsSupervisor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Supervisor').exists()


class IsDeanOrHOD(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name__in=['Dean', 'HOD']).exists()


class IsStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_staff
