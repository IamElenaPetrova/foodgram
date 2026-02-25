import datetime
from http import HTTPStatus

from django.db.models import (Count, Prefetch, Sum, F)
from django.http import FileResponse
from django.urls import reverse
from djoser.views import UserViewSet as DjoserViewSet
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, SAFE_METHODS
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .serializers import (IngredientSerializer,
                          UserBaseSerializer, UserSerializerSetAndDelAvatar,
                          UserSerializerWithRecipeCount,
                          FollowSerializer, RecipeReadSerializer,
                          RecipeFavoriteSerializer,
                          RecipeShoppingCartSerializer,
                          RecipeWriteSerializer, TagSerializer)
from recipes.models import (Ingredient, Recipe, RecipeFavorite,
                            RecipeIngredient, ShoppingCart, Tag)
from users.models import Follow
from recipes.constants import (
    ERROR_EMPTY_SHOPPING_CART,
    ERROR_NO_DATA, ERROR_NO_FOLLOW,
    ERROR_NO_RECIPE_FOUND
)
from .filters import NameSearchFilter, RecipeFilter
from .pagination import RecipePagination
from .permissions import IsOwnerOrReadOnly
from .utils import (generate_pdf_shopping_cart,
                    encode_recipe_id)


class UserViewSet(DjoserViewSet):
    pagination_class = RecipePagination
    http_method_names = ('get', 'post', 'put', 'delete')

    @action(detail=False, methods=('get',),
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        serializer = UserBaseSerializer(
            request.user, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=('put',),
            url_path='me/avatar', permission_classes=(IsAuthenticated,))
    def me_avatar(self, request):
        if 'avatar' not in request.data:
            return Response(
                {'avatar': [ERROR_NO_DATA]},
                status=HTTPStatus.BAD_REQUEST
            )
        serializer = UserSerializerSetAndDelAvatar(
            request.user, data=request.data,
            partial=True, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @me_avatar.mapping.delete
    def delete_avatar(self, request):
        request.user.avatar.delete(save=True)
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(detail=True, methods=('post',),
            permission_classes=(IsAuthenticated,),
            url_path='subscribe', url_name='subscribe')
    def subscribe(self, request, *args, **kwargs):
        author = self.get_object()
        serializer = FollowSerializer(
            data={'author': author.id},
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, *args, **kwargs):
        author = self.get_object()
        deleted_count, _ = Follow.objects.filter(
            user=request.user, author=author
        ).delete()
        if deleted_count:
            return Response(status=HTTPStatus.NO_CONTENT)
        return Response({'author': [ERROR_NO_FOLLOW]},
                        status=HTTPStatus.BAD_REQUEST)

    @action(detail=False, methods=('get',),
            url_path='subscriptions', url_name='subscriptions')
    def subscriptions(self, request, *args, **kwargs):
        queryset = self.get_queryset().filter(
            follows_to_author__user=request.user).annotate(
                recipes_count=Count('recipes')
        ).order_by('username')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserSerializerWithRecipeCount(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = UserSerializerWithRecipeCount(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data, status=HTTPStatus.OK)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (NameSearchFilter,)
    search_fields = ('^name',)
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    http_method_names = ('get', 'post', 'patch', 'delete')
    pagination_class = RecipePagination
    permission_classes = (IsOwnerOrReadOnly,)
    filter_backends = (filters.SearchFilter, DjangoFilterBackend,
                       filters.OrderingFilter)
    filterset_class = RecipeFilter

    def get_queryset(self):
        user = self.request.user
        base_queryset = Recipe.objects.select_related(
            'author'
        ).prefetch_related(
            'tags', 'recipeingredients__ingredient')
        if user.is_authenticated:
            return base_queryset.prefetch_related(
                Prefetch(
                    'favorite_recipes',
                    queryset=RecipeFavorite.objects.filter(user=user),
                    to_attr='user_favorites'
                ),
                Prefetch(
                    'shopping_cart_recipes',
                    queryset=ShoppingCart.objects.filter(user=user),
                    to_attr='user_shopping_cart'
                )
            )
        return base_queryset

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @action(detail=True, methods=('get',),
            url_path='get-link',
            url_name='get-link',
            permission_classes=(AllowAny,))
    def get_short_link(self, request, *args, **kwargs):
        recipe = self.get_object()
        short_hash = encode_recipe_id(recipe.id)
        short_path = reverse(
            'recipe_short_link',
            kwargs={'short_hash': short_hash}
        )
        short_link = request.build_absolute_uri(short_path)
        return Response({'short-link': short_link}, status=HTTPStatus.OK)

    def create_user_recipe_relation(self, serializer_class, pk):
        user = self.request.user
        recipe = self.get_object()
        serializer = serializer_class(
            data={'recipe': recipe.id}, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user,)
        return Response(serializer.data, status=HTTPStatus.CREATED)

    def delete_user_recipe_relation(self, model, pk):
        user = self.request.user
        recipe = self.get_object()
        deleted_count, _ = model.objects.filter(user=user,
                                                recipe_id=recipe.id).delete()
        return Response(
            status=HTTPStatus.NO_CONTENT
        ) if deleted_count else Response(
            {'errors': ERROR_NO_RECIPE_FOUND},
            status=HTTPStatus.BAD_REQUEST)

    @action(detail=True, methods=('post',),
            url_path='favorite',
            url_name='favorite',
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk=None):
        return self.create_user_recipe_relation(
            serializer_class=RecipeFavoriteSerializer, pk=pk)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        return self.delete_user_recipe_relation(
            model=RecipeFavorite, pk=pk)

    @action(detail=True, methods=('post',),
            url_path='shopping_cart',
            url_name='shopping_cart',
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk=None):
        return self.create_user_recipe_relation(
            serializer_class=RecipeShoppingCartSerializer,
            pk=pk)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        return self.delete_user_recipe_relation(
            model=ShoppingCart, pk=pk)

    @action(detail=False, methods=('get',),
            url_path='download_shopping_cart',
            url_name='download_shopping_cart',
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request, *args, **kwargs):
        shopping_cart = RecipeIngredient.objects.filter(
            recipe__shopping_cart_recipes__user=request.user
        ).values(
            name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit'),
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('name')
        if not shopping_cart.exists():
            return Response({'detail': ERROR_EMPTY_SHOPPING_CART},
                            status=HTTPStatus.BAD_REQUEST)
        pdf_buffer = generate_pdf_shopping_cart(shopping_cart)
        current_date = datetime.datetime.now().strftime('%Y%m%d')
        filename = f'shopping_list_{current_date}.pdf'
        return FileResponse(pdf_buffer, as_attachment=True,
                            filename=filename, content_type='application/pdf')
