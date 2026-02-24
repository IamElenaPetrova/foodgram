from rest_framework.pagination import PageNumberPagination

from foodgram.constants import PAGE_SIZE


class RecipePagination(PageNumberPagination):
    """ Кастомная пагинация с константой PAGE_SIZE и параметром limit. """

    page_size = PAGE_SIZE
    page_size_query_param = 'limit'
