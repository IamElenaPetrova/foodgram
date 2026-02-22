from django.http import HttpResponsePermanentRedirect

from .models import Recipe
from api.utils import decode_recipe_hash


def recipe_by_short_link(request, short_hash):
    """ Функция редиректа на рецепт по закодированной короткой ссылке. """

    recipe_id = decode_recipe_hash(short_hash)
    try:
        recipe = Recipe.objects.get(id=recipe_id)
        redirect_url = request.build_absolute_uri(
            f'/recipes/{recipe.id}/'
        )
    except Recipe.DoesNotExist:
        redirect_url = request.build_absolute_uri('/not_found')
    return HttpResponsePermanentRedirect(redirect_url)
