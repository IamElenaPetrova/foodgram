from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, IngredientViewSet, RecipeViewSet, TagViewSet


app_name = 'api'

rout_v1 = DefaultRouter()
rout_v1.register('ingredients', IngredientViewSet, basename='ingredients')
rout_v1.register('tags', TagViewSet, basename='tags')
rout_v1.register('recipes', RecipeViewSet, basename='recipes')
rout_v1.register(r'users', UserViewSet, basename='users')


urlpatterns = [
    path('', include(rout_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
