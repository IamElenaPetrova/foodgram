import csv

from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient


class Command(BaseCommand):
    help = ('Import ingredients data from CSV file to DB')

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        try:
            with open(csv_file_path, encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    name, unit = row
                    Ingredient.objects.get_or_create(
                        name=name, measurement_unit=unit)
        except FileNotFoundError:
            raise CommandError(f'{csv_file_path} file does not exist')
        except Exception as e:
            raise CommandError(f'Data import failed: {e}')

        self.stdout.write(self.style.SUCCESS(
            'Ingredients successfully loaded.'))
