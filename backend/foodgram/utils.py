import os

from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


def register_dejavu_fonts(base_dir):
    """ DejaVu шрифты для поддержки кириллицы. """

    font_paths = {
        'DejaVu': os.path.join(base_dir, 'fonts', 'DejaVuSans.ttf'),
        'DejaVu-Bold': os.path.join(base_dir, 'fonts', 'DejaVuSans-Bold.ttf'),
    }

    for font_name, font_path in font_paths.items():
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_path))
            except Exception as e:
                print(f'Ошибка регистрации шрифта {font_name}: {e}')
        else:
            print(f'Файл шрифта не найден: {font_path}')
