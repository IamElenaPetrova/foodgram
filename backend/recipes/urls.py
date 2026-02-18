from django.urls import path

from .views import recipe_by_short_link

urlpatterns = [
    path(
        's/<str:short_hash>/',
        recipe_by_short_link,
        name='recipe_short_link'),
]
