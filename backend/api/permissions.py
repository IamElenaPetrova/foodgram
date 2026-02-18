from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """ Разрешено на чтение или автору. """

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user)


class IsOwner(permissions.BasePermission):
    """ Разрешено только автору. """

    def has_object_permission(self, request, view, obj):
        return (obj.author == request.user)
