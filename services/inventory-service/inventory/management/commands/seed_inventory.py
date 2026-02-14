from django.core.management.base import BaseCommand
from inventory.models import Inventory
import random

class Command(BaseCommand):
    help = 'Seed the database with sample inventory data'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=1000, help='Number of inventory entries to create')

    def handle(self, *args, **options):
        count = options['count']

        self.stdout.write(f'Creating {count} inventory entries...')

        inventory_created = 0
        existing_product_ids = set()

        # Get existing product_ids to avoid duplicates
        existing_inventory = Inventory.objects.all()
        existing_product_ids = set(item.product_id for item in existing_inventory)

        for product_id in range(1, count + 1):
            if product_id in existing_product_ids:
                continue

            # Generate random inventory quantities
            # Most products will have stock between 0-1000, some will be out of stock
            if random.random() < 0.1:  # 10% chance of being out of stock
                quantity = 0
            else:
                quantity = random.randint(1, 1000)

            # Reserved quantity is usually less than total quantity
            reserved_quantity = random.randint(0, min(quantity, 100))

            Inventory.objects.create(
                product_id=product_id,
                quantity=quantity,
                reserved_quantity=reserved_quantity
            )

            inventory_created += 1

            if inventory_created % 100 == 0:
                self.stdout.write(f'Created {inventory_created} inventory entries...')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {inventory_created} inventory entries')
        )