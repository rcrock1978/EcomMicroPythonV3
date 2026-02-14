from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Inventory
from .serializers import InventorySerializer


class InventoryModelTest(TestCase):
    """Test cases for Inventory model"""

    def setUp(self):
        """Set up test data"""
        self.inventory = Inventory.objects.create(
            product_id=1,
            quantity=100,
            reserved_quantity=10
        )

    def test_inventory_creation(self):
        """Test that an inventory can be created with valid data"""
        self.assertEqual(self.inventory.product_id, 1)
        self.assertEqual(self.inventory.quantity, 100)
        self.assertEqual(self.inventory.reserved_quantity, 10)
        self.assertIsNotNone(self.inventory.id)
        self.assertIsNotNone(self.inventory.updated_at)

    def test_inventory_str_method(self):
        """Test the string representation of Inventory model"""
        self.assertEqual(str(self.inventory), "Inventory for product 1")

    def test_inventory_field_constraints(self):
        """Test field constraints and uniqueness"""
        # Test unique constraint on product_id
        with self.assertRaises(Exception):  # Should raise IntegrityError for duplicate product_id
            Inventory.objects.create(
                product_id=1,  # Same as existing inventory
                quantity=50
            )

    def test_inventory_default_values(self):
        """Test default field values"""
        inventory = Inventory.objects.create(
            product_id=2
        )
        self.assertEqual(inventory.quantity, 0)
        self.assertEqual(inventory.reserved_quantity, 0)

    def test_inventory_available_quantity(self):
        """Test available quantity calculation"""
        # Available quantity = total quantity - reserved quantity
        self.assertEqual(self.inventory.quantity - self.inventory.reserved_quantity, 90)

    def test_inventory_negative_quantities(self):
        """Test that negative quantities are allowed (for edge cases)"""
        inventory = Inventory.objects.create(
            product_id=3,
            quantity=-5,  # Negative quantity
            reserved_quantity=0
        )
        self.assertEqual(inventory.quantity, -5)


class InventorySerializerTest(TestCase):
    """Test cases for Inventory serializer"""

    def setUp(self):
        """Set up test data"""
        self.inventory_data = {
            'product_id': 1,
            'quantity': 100,
            'reserved_quantity': 10
        }
        self.inventory = Inventory.objects.create(**self.inventory_data)

    def test_serializer_contains_expected_fields(self):
        """Test that serializer contains all expected fields"""
        serializer = InventorySerializer(self.inventory)
        data = serializer.data
        expected_fields = ['id', 'product_id', 'quantity', 'reserved_quantity', 'updated_at']
        for field in expected_fields:
            self.assertIn(field, data)

    def test_serializer_data_types(self):
        """Test that serializer returns correct data types"""
        serializer = InventorySerializer(self.inventory)
        data = serializer.data
        self.assertIsInstance(data['id'], int)
        self.assertIsInstance(data['product_id'], int)
        self.assertIsInstance(data['quantity'], int)
        self.assertIsInstance(data['reserved_quantity'], int)
        self.assertIsNotNone(data['updated_at'])

    def test_serializer_create(self):
        """Test serializer create functionality"""
        create_data = {
            'product_id': 2,
            'quantity': 50,
            'reserved_quantity': 5
        }
        serializer = InventorySerializer(data=create_data)
        self.assertTrue(serializer.is_valid())
        inventory = serializer.save()
        self.assertEqual(inventory.product_id, 2)
        self.assertEqual(inventory.quantity, 50)
        self.assertEqual(inventory.reserved_quantity, 5)

    def test_serializer_update(self):
        """Test serializer update functionality"""
        update_data = {
            'product_id': 1,
            'quantity': 200,
            'reserved_quantity': 20
        }
        serializer = InventorySerializer(self.inventory, data=update_data)
        self.assertTrue(serializer.is_valid())
        updated_inventory = serializer.save()
        self.assertEqual(updated_inventory.product_id, 1)
        self.assertEqual(updated_inventory.quantity, 200)
        self.assertEqual(updated_inventory.reserved_quantity, 20)

    def test_serializer_validation_valid_data(self):
        """Test serializer validation with valid data"""
        valid_data = {
            'product_id': 3,
            'quantity': 75,
            'reserved_quantity': 15
        }
        serializer = InventorySerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(len(serializer.errors), 0)

    def test_serializer_validation_missing_product_id(self):
        """Test serializer validation with missing product_id"""
        data = {
            'quantity': 100,
            'reserved_quantity': 10
        }
        serializer = InventorySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('product_id', serializer.errors)

    def test_serializer_validation_duplicate_product_id(self):
        """Test serializer validation with duplicate product_id"""
        # Create first inventory
        Inventory.objects.create(
            product_id=10,
            quantity=50
        )

        # Try to create second inventory with same product_id
        data = {
            'product_id': 10,  # Same as existing inventory
            'quantity': 25
        }
        serializer = InventorySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('product_id', serializer.errors)

    def test_serializer_validation_negative_quantity(self):
        """Test serializer validation with negative quantity (should be allowed)"""
        data = {
            'product_id': 4,
            'quantity': -10,
            'reserved_quantity': 0
        }
        serializer = InventorySerializer(data=data)
        self.assertTrue(serializer.is_valid())  # Negative quantities should be allowed

    def test_serializer_validation_reserved_greater_than_quantity(self):
        """Test serializer validation when reserved quantity > total quantity (should be allowed)"""
        data = {
            'product_id': 5,
            'quantity': 10,
            'reserved_quantity': 20  # More than quantity
        }
        serializer = InventorySerializer(data=data)
        self.assertTrue(serializer.is_valid())  # Should be allowed (business logic validation elsewhere)


class InventoryAPITest(APITestCase):
    """Test cases for Inventory API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.inventory_data = {
            'product_id': 1,
            'quantity': 100,
            'reserved_quantity': 10
        }
        self.inventory = Inventory.objects.create(**self.inventory_data)

    def test_get_all_inventories(self):
        """Test GET /api/inventory/ returns all inventories"""
        response = self.client.get('/api/inventory/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)

        # Check that our test inventory is in the response
        inventory_data = response.data[0]
        self.assertEqual(inventory_data['product_id'], 1)
        self.assertEqual(inventory_data['quantity'], 100)
        self.assertEqual(inventory_data['reserved_quantity'], 10)

    def test_create_inventory_valid_data(self):
        """Test POST /api/inventory/ with valid data"""
        new_inventory_data = {
            'product_id': 2,
            'quantity': 50,
            'reserved_quantity': 5
        }
        response = self.client.post('/api/inventory/', new_inventory_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check response data
        self.assertEqual(response.data['product_id'], 2)
        self.assertEqual(response.data['quantity'], 50)
        self.assertEqual(response.data['reserved_quantity'], 5)

        # Check database
        inventory = Inventory.objects.get(product_id=2)
        self.assertEqual(inventory.quantity, 50)
        self.assertEqual(inventory.reserved_quantity, 5)

    def test_create_inventory_missing_fields(self):
        """Test POST /api/inventory/ with missing required fields"""
        incomplete_data = {
            'quantity': 100,
            'reserved_quantity': 10
            # Missing product_id
        }
        response = self.client.post('/api/inventory/', incomplete_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('product_id', response.data)

    def test_create_inventory_duplicate_product_id(self):
        """Test POST /api/inventory/ with duplicate product_id"""
        duplicate_data = {
            'product_id': 1,  # Same as existing inventory
            'quantity': 50
        }
        response = self.client.post('/api/inventory/', duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('product_id', response.data)

    def test_api_response_format(self):
        """Test that API responses have correct format"""
        response = self.client.get('/api/inventory/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that response is a list
        self.assertIsInstance(response.data, list)

        # If there are inventories, check the structure of the first one
        if response.data:
            inventory_data = response.data[0]
            required_fields = ['id', 'product_id', 'quantity', 'reserved_quantity', 'updated_at']
            for field in required_fields:
                self.assertIn(field, inventory_data)


class InventoryIntegrationTest(TestCase):
    """Integration tests for Inventory functionality"""

    def test_full_inventory_lifecycle(self):
        """Test creating, reading, and verifying an inventory"""
        # Create inventory
        inventory = Inventory.objects.create(
            product_id=100,
            quantity=200,
            reserved_quantity=20
        )

        # Verify creation
        self.assertEqual(inventory.product_id, 100)
        self.assertEqual(inventory.quantity, 200)
        self.assertEqual(inventory.reserved_quantity, 20)

        # Test serialization
        serializer = InventorySerializer(inventory)
        data = serializer.data
        self.assertEqual(data['product_id'], 100)
        self.assertEqual(data['quantity'], 200)
        self.assertEqual(data['reserved_quantity'], 20)

        # Verify in database
        db_inventory = Inventory.objects.get(product_id=100)
        self.assertEqual(db_inventory.quantity, 200)
        self.assertEqual(str(db_inventory), "Inventory for product 100")

    def test_bulk_inventory_operations(self):
        """Test operations with multiple inventories"""
        # Create multiple inventories
        inventories_data = [
            {'product_id': i, 'quantity': i * 10, 'reserved_quantity': i * 2}
            for i in range(10, 15)  # product_ids 10-14
        ]

        created_inventories = []
        for inventory_data in inventories_data:
            inventory = Inventory.objects.create(**inventory_data)
            created_inventories.append(inventory)

        # Verify all inventories were created (5 new inventories)
        self.assertEqual(Inventory.objects.count(), 5)

        # Test bulk serialization
        serializer = InventorySerializer(created_inventories, many=True)
        data = serializer.data
        self.assertEqual(len(data), 5)

        # Verify each inventory in serialized data
        product_ids = [inv['product_id'] for inv in data]
        for i in range(10, 15):
            self.assertIn(i, product_ids)

    def test_inventory_quantity_operations(self):
        """Test inventory quantity operations"""
        inventory = Inventory.objects.create(
            product_id=50,
            quantity=100,
            reserved_quantity=0
        )

        # Test reserving quantity
        inventory.reserved_quantity = 20
        inventory.save()

        # Verify available quantity
        self.assertEqual(inventory.quantity - inventory.reserved_quantity, 80)

        # Test updating quantity
        inventory.quantity = 150
        inventory.save()

        # Refresh from database and verify
        inventory.refresh_from_db()
        self.assertEqual(inventory.quantity, 150)
        self.assertEqual(inventory.reserved_quantity, 20)
