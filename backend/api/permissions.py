from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """ Разрешено на чтение всем, измнение - автору,
    создание - авторизованным. """

    def has_permission(self, request, view):
        return ((request.method in permissions.SAFE_METHODS)
                or (request.user and request.user.is_authenticated))

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user)
