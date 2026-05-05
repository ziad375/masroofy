from django.core.management.base import BaseCommand
from core.models import Category

DEFAULT_CATEGORIES = [
    'Food', 'Transport', 'Housing', 'Healthcare',
    'Education', 'Entertainment', 'Shopping', 'Salary',
    'Freelance', 'Investment', 'Other'
]

class Command(BaseCommand):
    help = 'Seed default system categories'

    def handle(self, *args, **kwargs):
        for name in DEFAULT_CATEGORIES:
            Category.objects.get_or_create(name=name, source='system')
            self.stdout.write(f'  ✓ {name}')
        self.stdout.write(self.style.SUCCESS('Categories seeded successfully.'))
