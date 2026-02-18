import datetime

from django.http import HttpResponse
from django.db.models import (Count, Prefetch, Sum, Window, F)
from django.db.models.functions import RowNumber
from django.urls import reverse
from djoser.views import UserViewSet as DjoserViewSet
from rest_framework import status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .serializers import (IngredientSerializer, User,
                          UserBaseSerializer, UserSerializerSetAndDelAvatar,
                          UserSerializerWithRecipeCount,
                          FollowSerializer, RecipeReadSerializer,
                          RecipeFavoriteSerializer,
                          RecipeReducedSerializer,
                          RecipeShoppingCartSerializer,
                          RecipeWriteSerializer, TagSerializer)

from recipes.models import (Ingredient, Recipe, RecipeFavorite,
                            RecipeIngredient, ShoppingCart, Tag)
from recipes.constants import (ERROR_AVATAR_IS_NOT_FOUND,
                               ERROR_EMPTY_SHOPPING_CART,
                               ERROR_NO_DATA, ERROR_NO_FOLLOW,
                               ERROR_NO_RECIPE_IN_FAVORITE,
                               ERROR_NO_RECIPE_IN_SHOPPING_CART)
from .filters import NameSearchFilter, RecipeFilter
from .pagination import RecipePagination
from .permissions import IsOwner
from .utils import (generate_pdf_shopping_cart,
                    encode_recipe_id)


class UserViewSet(DjoserViewSet):
    pagination_class = RecipePagination
    http_method_names = ['get', 'post', 'put', 'delete']

    def get_permissions(self):
        if self.action in ('me', 'me_avatar', 'subscribe', 'subscriptions'):
            return (IsAuthenticated(),)
        elif self.action in ('list', 'create', 'retrieve'):
            return (AllowAny(),)
        return super().get_permissions()

    def get_serializer_class(self, *args, **kwargs):
        if self.action == 'me':
            return UserBaseSerializer
        if self.action == 'me_avatar':
            return UserSerializerSetAndDelAvatar
        if self.action == 'subscribe':
            return FollowSerializer
        if self.action == 'subscriptions':
            return UserSerializerWithRecipeCount
        return super().get_serializer_class(*args, **kwargs)

    def get_queryset(self):
        base_queryset = User.objects.all()
        queryset = base_queryset.annotate(
            recipes_count=Count('recipes', distinct=True)
        )
        recipes_limit = self.request.query_params.get('recipes_limit')
        try:
            recipes_limit = int(recipes_limit) if recipes_limit else None
        except ValueError:
            recipes_limit = None
        if recipes_limit is not None and recipes_limit > 0:
            limited_recipes = Recipe.objects.annotate(
                row_number=Window(
                    expression=RowNumber(),
                    partition_by=[F('author')],
                    order_by=F('pub_date').desc()
                )
            ).filter(row_number__lte=recipes_limit)
            queryset = queryset.prefetch_related(
                Prefetch(
                    'recipes',
                    queryset=limited_recipes,
                    to_attr='limited_recipes'
                )
            )
        else:
            queryset = queryset.prefetch_related('recipes')
        return queryset

    @action(detail=False, methods=('put', 'delete', ),
            url_path='me/avatar', url_name='me_avatar')
    def me_avatar(self, request):
        if request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response(
                    {'avatar': [ERROR_NO_DATA]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = self.get_serializer(
                request.user,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            if request.user.avatar:
                request.user.avatar.delete(save=True)
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'detail': [ERROR_AVATAR_IS_NOT_FOUND]},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=('post', 'delete',),
            url_path='subscribe', url_name='subscribe')
    def subscribe(self, request, *args, **kwargs):
        user_being_followed = self.get_object()
        if request.method == 'POST':
            serializer = self.get_serializer(data={
                'user_being_followed': user_being_followed.id,
            }, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            user_with_limit = self.get_queryset().get(
                pk=user_being_followed.pk)
            user_serializer = UserSerializerWithRecipeCount(
                user_with_limit, context={'request': request}
            )
            return Response(user_serializer.data,
                            status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            user_is_following = request.user
            is_subscribed = user_is_following.following.filter(
                user_being_followed=user_being_followed).exists()
            if is_subscribed:
                user_is_following.following.filter(
                    user_being_followed=user_being_followed).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {'user_being_followed': [ERROR_NO_FOLLOW]},
                    status=status.HTTP_400_BAD_REQUEST
                )

    @action(detail=False, methods=('get',),
            url_path='subscriptions', url_name='subscriptions')
    def subscriptions(self, request, *args, **kwargs):
        followed_users_ids = request.user.following.values_list(
            'user_being_followed', flat=True)
        followed_users = self.get_queryset().filter(
            id__in=followed_users_ids)

        page = self.paginate_queryset(followed_users)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(followed_users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
    http_method_names = ['get', 'post', 'patch', 'delete']
    pagination_class = RecipePagination
    filter_backends = (filters.SearchFilter, DjangoFilterBackend,
                       filters.OrderingFilter)
    filterset_class = RecipeFilter

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return (AllowAny(),)
        elif self.action in ('create',):
            return (IsAuthenticated(),)
        elif self.action in ('partial_update', 'destroy'):
            return (IsAuthenticated(), IsOwner(),)
        return super().get_permissions()

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

    def get_shopping_cart_queryset(self):
        user = self.request.user
        shopping_cart_queryset = RecipeIngredient.objects.filter(
            recipe__shopping_cart_recipes__user=user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')
        return shopping_cart_queryset

    def get_serializer_class(self):
        if self.action in ('retrieve', 'list'):
            return RecipeReadSerializer
        elif self.action in ('create', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    @action(detail=True, methods=['get'],
            url_path='get-link',
            url_name='get-link',
            permission_classes=[AllowAny])
    def get_short_link(self, request, *args, **kwargs):
        recipe = self.get_object()
        short_hash = encode_recipe_id(recipe.id)
        short_path = reverse(
            'recipe_short_link',
            kwargs={'short_hash': short_hash}
        )
        short_link = request.build_absolute_uri(short_path)
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    @action(detail=True, methods=('post', 'delete',),
            url_path='favorite',
            url_name='favorite',
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, *args, **kwargs):
        recipe = self.get_object()
        if request.method == 'POST':
            serializer = RecipeFavoriteSerializer(data={
                'recipe': recipe.id,
            }, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            recipe_serializer = RecipeReducedSerializer(
                recipe, context={'request': request}
            )
            return Response(recipe_serializer.data,
                            status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            recipe = self.get_object()
            user = request.user
            is_favorited = user.favorite_recipes.filter(recipe=recipe).exists()
            if is_favorited:
                user.favorite_recipes.filter(recipe=recipe).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {'recipe': [ERROR_NO_RECIPE_IN_FAVORITE]},
                    status=status.HTTP_400_BAD_REQUEST
                )

    @action(detail=True, methods=('post', 'delete',),
            url_path='shopping_cart',
            url_name='shopping_cart',
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, *args, **kwargs):
        recipe = self.get_object()
        if request.method == 'POST':
            serializer = RecipeShoppingCartSerializer(data={
                'recipe': recipe.id,
            }, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            recipe_serializer = RecipeReducedSerializer(
                recipe, context={'request': request}
            )
            return Response(recipe_serializer.data,
                            status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            user = request.user
            if user.shopping_cart_recipes.filter(recipe=recipe).exists():
                user.shopping_cart_recipes.filter(recipe=recipe).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {'recipe': [ERROR_NO_RECIPE_IN_SHOPPING_CART]},
                    status=status.HTTP_400_BAD_REQUEST
                )

    @action(detail=False, methods=('get',),
            url_path='download_shopping_cart',
            url_name='download_shopping_cart',
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request, *args, **kwargs):
        shopping_cart_to_download = self.get_shopping_cart_queryset()
        if not shopping_cart_to_download.exists():
            return Response({'detail': ERROR_EMPTY_SHOPPING_CART},
                            status=400)
        pdf = generate_pdf_shopping_cart(
            shopping_cart=shopping_cart_to_download)
        response = HttpResponse(pdf, content_type='application/pdf')
        current_date = datetime.datetime.now().strftime("%Y%m%d")
        filename = f'shopping_list_{current_date}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
