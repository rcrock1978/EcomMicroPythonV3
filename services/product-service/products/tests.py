from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
from .models import Product
from .serializers import ProductSerializer


class ProductModelTest(TestCase):
    """Test cases for the Product model"""

    def setUp(self):
        """Set up test data"""
        self.product = Product.objects.create(
            name="Test Product",
            description="This is a test product description",
            price=Decimal('29.99')
        )

    def test_product_creation(self):
        """Test that a product can be created with valid data"""
        self.assertEqual(self.product.name, "Test Product")
        self.assertEqual(self.product.description, "This is a test product description")
        self.assertEqual(self.product.price, Decimal('29.99'))
        self.assertIsNotNone(self.product.id)

    def test_product_str_method(self):
        """Test the string representation of Product model"""
        self.assertEqual(str(self.product), "Test Product")

    def test_product_price_decimal_places(self):
        """Test that price field handles decimal places correctly"""
        product = Product.objects.create(
            name="Decimal Test",
            description="Testing decimal precision",
            price=Decimal('19.999')
        )
        # PostgreSQL rounds to 2 decimal places when storing
        product.refresh_from_db()
        self.assertEqual(product.price, Decimal('20.00'))

    def test_product_fields_max_length(self):
        """Test field constraints"""
        # Test name max length
        long_name = "A" * 255  # Max length is 255
        product = Product.objects.create(
            name=long_name,
            description="Test description",
            price=Decimal('10.00')
        )
        self.assertEqual(len(product.name), 255)

    def test_product_required_fields(self):
        """Test that required fields cannot be null"""
        from django.core.exceptions import ValidationError

        # Test missing name - should raise ValidationError
        product = Product(name="", description="Test", price=Decimal('10.00'))
        with self.assertRaises(ValidationError):
            product.full_clean()

        # Test missing price - should raise ValidationError
        product = Product(name="Test Product", description="Test description", price=None)
        with self.assertRaises(ValidationError):
            product.full_clean()


class ProductSerializerTest(TestCase):
    """Test cases for the ProductSerializer"""

    def setUp(self):
        """Set up test data"""
        self.product_data = {
            'name': 'Test Product',
            'description': 'Test description',
            'price': '29.99'
        }
        self.product = Product.objects.create(**self.product_data)
        self.serializer = ProductSerializer(instance=self.product)

    def test_serializer_contains_expected_fields(self):
        """Test that serializer contains all expected fields"""
        data = self.serializer.data
        self.assertEqual(set(data.keys()), {'id', 'name', 'description', 'price'})

    def test_serializer_data_types(self):
        """Test that serializer returns correct data types"""
        data = self.serializer.data
        self.assertIsInstance(data['id'], int)
        self.assertIsInstance(data['name'], str)
        self.assertIsInstance(data['description'], str)
        self.assertIsInstance(data['price'], str)  # DRF serializes Decimal as string

    def test_serializer_price_formatting(self):
        """Test that price is properly formatted"""
        data = self.serializer.data
        self.assertEqual(data['price'], '29.99')

    def test_serializer_validation_valid_data(self):
        """Test serializer validation with valid data"""
        serializer = ProductSerializer(data=self.product_data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_validation_invalid_price(self):
        """Test serializer validation with invalid price"""
        invalid_data = self.product_data.copy()
        invalid_data['price'] = 'invalid_price'
        serializer = ProductSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('price', serializer.errors)

    def test_serializer_validation_missing_name(self):
        """Test serializer validation with missing name"""
        invalid_data = self.product_data.copy()
        del invalid_data['name']
        serializer = ProductSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_serializer_validation_empty_name(self):
        """Test serializer validation with empty name"""
        invalid_data = self.product_data.copy()
        invalid_data['name'] = ''
        serializer = ProductSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_serializer_create(self):
        """Test serializer create functionality"""
        serializer = ProductSerializer(data=self.product_data)
        self.assertTrue(serializer.is_valid())
        product = serializer.save()
        self.assertIsInstance(product, Product)
        self.assertEqual(product.name, self.product_data['name'])

    def test_serializer_update(self):
        """Test serializer update functionality"""
        update_data = {
            'name': 'Updated Product',
            'description': 'Updated description',
            'price': '39.99'
        }
        serializer = ProductSerializer(instance=self.product, data=update_data)
        self.assertTrue(serializer.is_valid())
        updated_product = serializer.save()
        self.assertEqual(updated_product.name, 'Updated Product')
        self.assertEqual(updated_product.price, Decimal('39.99'))


class ProductAPITest(APITestCase):
    """Test cases for Product API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.product1 = Product.objects.create(
            name="Product 1",
            description="Description 1",
            price=Decimal('19.99')
        )
        self.product2 = Product.objects.create(
            name="Product 2",
            description="Description 2",
            price=Decimal('29.99')
        )
        self.valid_product_data = {
            'name': 'New Product',
            'description': 'New product description',
            'price': '39.99'
        }
        self.invalid_product_data = {
            'name': '',
            'description': 'Invalid product',
            'price': 'invalid'
        }

    def test_get_all_products(self):
        """Test GET /api/products/ returns all products"""
        url = reverse('product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Check that response contains expected products
        product_names = [product['name'] for product in response.data]
        self.assertIn('Product 1', product_names)
        self.assertIn('Product 2', product_names)

    def test_get_single_product(self):
        """Test GET /api/products/<id>/ returns single product"""
        url = reverse('product-detail', kwargs={'pk': self.product1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Product 1')
        self.assertEqual(response.data['price'], '19.99')

    def test_get_nonexistent_product(self):
        """Test GET /api/products/<id>/ for nonexistent product"""
        url = reverse('product-detail', kwargs={'pk': 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_product_valid_data(self):
        """Test POST /api/products/ with valid data"""
        url = reverse('product-list')
        response = self.client.post(url, self.valid_product_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Product')
        self.assertEqual(response.data['price'], '39.99')
        # Verify product was created in database
        self.assertEqual(Product.objects.count(), 3)

    def test_create_product_invalid_data(self):
        """Test POST /api/products/ with invalid data"""
        url = reverse('product-list')
        response = self.client.post(url, self.invalid_product_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        self.assertIn('price', response.data)
        # Verify no product was created
        self.assertEqual(Product.objects.count(), 2)

    def test_create_product_missing_fields(self):
        """Test POST /api/products/ with missing required fields"""
        url = reverse('product-list')
        incomplete_data = {'name': 'Incomplete Product'}
        response = self.client.post(url, incomplete_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('description', response.data)
        self.assertIn('price', response.data)

    def test_api_response_format(self):
        """Test that API responses have correct format"""
        url = reverse('product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that response is a list
        self.assertIsInstance(response.data, list)

        # Check structure of first product
        if response.data:
            product = response.data[0]
            self.assertIn('id', product)
            self.assertIn('name', product)
            self.assertIn('description', product)
            self.assertIn('price', product)

    def test_price_precision_in_api(self):
        """Test that price precision is maintained in API responses"""
        # Create product with specific decimal
        product = Product.objects.create(
            name="Precision Test",
            description="Testing price precision",
            price=Decimal('19.99')
        )
        url = reverse('product-detail', kwargs={'pk': product.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['price'], '19.99')


class ProductIntegrationTest(APITestCase):
    """Integration tests for product operations"""

    def test_full_product_lifecycle(self):
        """Test creating, reading, and verifying a product"""
        # Create product
        create_data = {
            'name': 'Lifecycle Product',
            'description': 'Testing full lifecycle',
            'price': '49.99'
        }
        create_url = reverse('product-list')
        create_response = self.client.post(create_url, create_data, format='json')
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        product_id = create_response.data['id']

        # Read product
        read_url = reverse('product-detail', kwargs={'pk': product_id})
        read_response = self.client.get(read_url)
        self.assertEqual(read_response.status_code, status.HTTP_200_OK)
        self.assertEqual(read_response.data['name'], 'Lifecycle Product')
        self.assertEqual(read_response.data['price'], '49.99')

        # Verify in list
        list_url = reverse('product-list')
        list_response = self.client.get(list_url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        product_names = [p['name'] for p in list_response.data]
        self.assertIn('Lifecycle Product', product_names)

    def test_bulk_operations(self):
        """Test operations with multiple products"""
        # Create multiple products
        products_data = [
            {'name': f'Bulk Product {i}', 'description': f'Description {i}', 'price': f'{10.00 + i}'}
            for i in range(1, 6)
        ]

        for product_data in products_data:
            url = reverse('product-list')
            response = self.client.post(url, product_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify all products exist
        url = reverse('product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

        # Verify each product is accessible individually
        for i, product_data in enumerate(products_data, 1):
            # Find the product in the list
            product = next(p for p in response.data if p['name'] == product_data['name'])
            detail_url = reverse('product-detail', kwargs={'pk': product['id']})
            detail_response = self.client.get(detail_url)
            self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
            self.assertEqual(detail_response.data['name'], product_data['name'])
