from hashids import Hashids
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

from django.conf import settings


def generate_pdf_shopping_cart(shopping_cart):
    """ Генерирует список покупок. """
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    p.setFont('DejaVu', 16)
    p.drawString(2 * cm, height - 2 * cm, 'Список покупок')
    y = height - 5 * cm
    p.setFont('DejaVu-Bold', 11)
    p.drawString(2 * cm, y, 'Ингредиент')
    p.drawString(12 * cm, y, 'Кол-во')
    p.drawString(15 * cm, y, 'Ед.')
    p.setFont('DejaVu', 10)
    for i, item in enumerate(shopping_cart, 1):
        y -= 0.7 * cm
        p.drawString(2 * cm, y, f'{i}. {item["ingredient__name"]}')
        p.drawString(12 * cm, y, str(item['total_amount']))
        p.drawString(15 * cm, y, item['ingredient__measurement_unit'])
    p.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def get_hashids():
    """ Инициализирует и возвращает объект Hashids."""
    salt = getattr(settings, 'HASHIDS_SALT', 'your-secret-salt-change-me')
    min_length = getattr(settings, 'HASHIDS_MIN_LENGTH', 8)
    alphabet = getattr(
        settings,
        'HASHIDS_ALPHABET',
        'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890')
    return Hashids(salt=salt, min_length=min_length, alphabet=alphabet)


def encode_recipe_id(recipe_id: int):
    """ Кодирует id рецепта. """
    hashids = get_hashids()
    return hashids.encode(recipe_id)


def decode_recipe_hash(hash_string: str):
    """ Декодирует hash_string. """
    hashids = get_hashids()
    decoded = hashids.decode(hash_string)
    return decoded[0] if decoded else None
