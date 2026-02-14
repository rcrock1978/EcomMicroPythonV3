from django.core.management.base import BaseCommand
from products.models import Product
import random
import faker

class Command(BaseCommand):
    help = 'Seed the database with sample products'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=1000, help='Number of products to create')

    def handle(self, *args, **options):
        count = options['count']
        fake = faker.Faker()

        # Product categories and sample data
        categories = [
            'Electronics', 'Clothing', 'Books', 'Home & Garden', 'Sports',
            'Beauty', 'Toys', 'Automotive', 'Health', 'Food'
        ]

        product_templates = {
            'Electronics': [
                ('Smartphone', 'Latest smartphone with advanced features', 299.99),
                ('Laptop', 'High-performance laptop for work and gaming', 899.99),
                ('Headphones', 'Wireless noise-cancelling headphones', 149.99),
                ('Smart Watch', 'Fitness tracking smartwatch', 249.99),
                ('Tablet', '10-inch tablet with high-resolution display', 349.99),
                ('Bluetooth Speaker', 'Portable wireless speaker', 79.99),
                ('Gaming Console', 'Next-generation gaming console', 499.99),
                ('Wireless Router', 'High-speed WiFi router', 129.99),
            ],
            'Clothing': [
                ('T-Shirt', 'Cotton crew neck t-shirt', 19.99),
                ('Jeans', 'Classic fit denim jeans', 49.99),
                ('Sneakers', 'Comfortable running sneakers', 79.99),
                ('Jacket', 'Waterproof outdoor jacket', 89.99),
                ('Dress', 'Elegant evening dress', 69.99),
                ('Sweater', 'Warm wool blend sweater', 39.99),
                ('Shorts', 'Casual cotton shorts', 24.99),
                ('Hat', 'Stylish baseball cap', 14.99),
            ],
            'Books': [
                ('Programming Guide', 'Comprehensive programming tutorial', 29.99),
                ('Novel', 'Bestselling fiction novel', 14.99),
                ('Cookbook', 'Delicious recipes from around the world', 24.99),
                ('Biography', 'Inspiring life story', 19.99),
                ('Textbook', 'Academic textbook for students', 89.99),
                ('Children\'s Book', 'Fun and educational for kids', 9.99),
                ('Self-Help', 'Personal development guide', 16.99),
                ('History Book', 'Fascinating historical account', 22.99),
            ],
            'Home & Garden': [
                ('Coffee Maker', 'Automatic drip coffee maker', 59.99),
                ('Blender', 'High-power kitchen blender', 79.99),
                ('Garden Hose', '50ft expandable garden hose', 34.99),
                ('Throw Pillow', 'Decorative throw pillow', 24.99),
                ('Lamp', 'Modern table lamp', 49.99),
                ('Plant Pot', 'Ceramic plant pot set', 19.99),
                ('Vacuum Cleaner', 'Cordless stick vacuum', 149.99),
                ('Bedding Set', 'Complete queen bedding set', 89.99),
            ],
            'Sports': [
                ('Yoga Mat', 'Non-slip exercise mat', 29.99),
                ('Dumbbells', 'Adjustable weight dumbbells', 49.99),
                ('Basketball', 'Official size basketball', 39.99),
                ('Tennis Racket', 'Professional tennis racket', 89.99),
                ('Swimming Goggles', 'Anti-fog swimming goggles', 14.99),
                ('Bike Helmet', 'Safety certified bike helmet', 34.99),
                ('Soccer Ball', 'Professional soccer ball', 24.99),
                ('Resistance Bands', 'Set of exercise resistance bands', 19.99),
            ],
            'Beauty': [
                ('Shampoo', 'Moisturizing shampoo', 12.99),
                ('Face Cream', 'Anti-aging face cream', 29.99),
                ('Lipstick', 'Long-lasting lipstick', 19.99),
                ('Perfume', 'Designer fragrance', 49.99),
                ('Hair Dryer', 'Professional hair dryer', 79.99),
                ('Nail Polish', 'Quick-dry nail polish', 7.99),
                ('Makeup Brush Set', 'Professional makeup brushes', 24.99),
                ('Sunscreen', 'SPF 50 sunscreen lotion', 15.99),
            ],
            'Toys': [
                ('Building Blocks', 'Creative building block set', 34.99),
                ('Stuffed Animal', 'Soft plush stuffed animal', 19.99),
                ('Board Game', 'Family board game', 24.99),
                ('Puzzle', '1000-piece jigsaw puzzle', 14.99),
                ('Remote Control Car', 'RC racing car', 39.99),
                ('Doll', 'Fashion doll with accessories', 29.99),
                ('Lego Set', 'Building construction set', 49.99),
                ('Action Figure', 'Superhero action figure', 12.99),
            ],
            'Automotive': [
                ('Car Wash Kit', 'Complete car cleaning kit', 24.99),
                ('Tire Pressure Gauge', 'Digital tire pressure gauge', 14.99),
                ('Car Air Freshener', 'Long-lasting car air freshener', 8.99),
                ('Phone Mount', 'Dashboard phone holder', 19.99),
                ('Car Vacuum', 'Handheld car vacuum cleaner', 29.99),
                ('Seat Covers', 'Universal car seat covers', 39.99),
                ('Oil Filter', 'Engine oil filter', 12.99),
                ('Car Battery', '12V car battery', 89.99),
            ],
            'Health': [
                ('Vitamins', 'Daily multivitamin supplement', 19.99),
                ('Blood Pressure Monitor', 'Digital blood pressure monitor', 49.99),
                ('Massage Gun', 'Deep tissue massage gun', 79.99),
                ('Fitness Tracker', 'Activity and sleep tracker', 99.99),
                ('Protein Powder', 'Whey protein powder', 34.99),
                ('First Aid Kit', 'Complete first aid kit', 24.99),
                ('Thermometer', 'Digital thermometer', 12.99),
                ('Yoga Block', 'Foam yoga block', 14.99),
            ],
            'Food': [
                ('Coffee Beans', 'Premium arabica coffee beans', 16.99),
                ('Tea Set', 'Assorted herbal tea collection', 19.99),
                ('Chocolate Bar', 'Artisan dark chocolate', 6.99),
                ('Spice Set', 'Essential cooking spices', 24.99),
                ('Protein Bars', 'High-protein snack bars', 14.99),
                ('Olive Oil', 'Extra virgin olive oil', 12.99),
                ('Granola', 'Organic granola mix', 8.99),
                ('Honey', 'Raw local honey', 9.99),
            ],
        }

        self.stdout.write(f'Creating {count} products...')

        products_created = 0
        for i in range(count):
            # Choose random category and template
            category = random.choice(categories)
            template = random.choice(product_templates[category])

            # Generate variations
            name = f"{template[0]} {fake.word().capitalize()}"
            description = f"{template[1]}. {fake.sentence()}"
            base_price = template[2]

            # Add some price variation (±20%)
            price_variation = random.uniform(-0.2, 0.2)
            price = round(base_price * (1 + price_variation), 2)

            Product.objects.create(
                name=name,
                description=description,
                price=price
            )

            products_created += 1

            if products_created % 100 == 0:
                self.stdout.write(f'Created {products_created} products...')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {products_created} products')
        )