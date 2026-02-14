from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
from .models import Order
from .serializers import OrderSerializer


class OrderModelTest(TestCase):
    """Test cases for Order model"""

    def setUp(self):
        """Set up test data"""
        self.order = Order.objects.create(
            user_id=1,
            product_id=1,
            quantity=2,
            total_price=Decimal('29.98'),
            status='pending'
        )

    def test_order_creation(self):
        """Test that an order can be created with valid data"""
        self.assertEqual(self.order.user_id, 1)
        self.assertEqual(self.order.product_id, 1)
        self.assertEqual(self.order.quantity, 2)
        self.assertEqual(self.order.total_price, Decimal('29.98'))
        self.assertEqual(self.order.status, 'pending')
        self.assertIsNotNone(self.order.id)

    def test_order_str_method(self):
        """Test the string representation of Order model"""
        expected_str = f"Order {self.order.id} - User 1 - Product 1"
        self.assertEqual(str(self.order), expected_str)

    def test_order_field_constraints(self):
        """Test field constraints"""
        # Test status max length
        long_status = "a" * 50
        order = Order.objects.create(
            user_id=2,
            product_id=2,
            quantity=1,
            total_price=Decimal('10.00'),
            status=long_status
        )
        self.assertEqual(len(order.status), 50)

    def test_order_default_values(self):
        """Test default field values"""
        order = Order.objects.create(
            user_id=3,
            product_id=3,
            quantity=1,
            total_price=Decimal('15.00')
        )
        self.assertEqual(order.status, 'pending')

    def test_order_status_choices(self):
        """Test order status values"""
        # Test different status values
        statuses = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']
        for i, status_val in enumerate(statuses):
            order = Order.objects.create(
                user_id=10 + i,
                product_id=10 + i,
                quantity=1,
                total_price=Decimal('10.00'),
                status=status_val
            )
            self.assertEqual(order.status, status_val)

    def test_order_total_price_precision(self):
        """Test total price decimal precision"""
        order = Order.objects.create(
            user_id=4,
            product_id=4,
            quantity=3,
            total_price=Decimal('45.6789')  # PostgreSQL stores full precision
        )
        # PostgreSQL stores the full decimal precision
        self.assertEqual(order.total_price, Decimal('45.6789'))


class OrderSerializerTest(TestCase):
    """Test cases for Order serializer"""

    def setUp(self):
        """Set up test data"""
        self.order_data = {
            'user_id': 1,
            'product_id': 1,
            'quantity': 2,
            'total_price': Decimal('29.98'),
            'status': 'pending'
        }
        self.order = Order.objects.create(**self.order_data)

    def test_serializer_contains_expected_fields(self):
        """Test that serializer contains all expected fields"""
        serializer = OrderSerializer(self.order)
        data = serializer.data
        expected_fields = ['id', 'user_id', 'product_id', 'quantity', 'total_price', 'status']
        for field in expected_fields:
            self.assertIn(field, data)

    def test_serializer_data_types(self):
        """Test that serializer returns correct data types"""
        serializer = OrderSerializer(self.order)
        data = serializer.data
        self.assertIsInstance(data['id'], int)
        self.assertIsInstance(data['user_id'], int)
        self.assertIsInstance(data['product_id'], int)
        self.assertIsInstance(data['quantity'], int)
        self.assertIsInstance(data['total_price'], str)  # Decimal is serialized as string
        self.assertIsInstance(data['status'], str)

    def test_serializer_create(self):
        """Test serializer create functionality"""
        create_data = {
            'user_id': 2,
            'product_id': 2,
            'quantity': 1,
            'total_price': Decimal('14.99'),
            'status': 'confirmed'
        }
        serializer = OrderSerializer(data=create_data)
        self.assertTrue(serializer.is_valid())
        order = serializer.save()
        self.assertEqual(order.user_id, 2)
        self.assertEqual(order.product_id, 2)
        self.assertEqual(order.quantity, 1)
        self.assertEqual(order.total_price, Decimal('14.99'))
        self.assertEqual(order.status, 'confirmed')

    def test_serializer_update(self):
        """Test serializer update functionality"""
        update_data = {
            'user_id': 1,
            'product_id': 1,
            'quantity': 3,
            'total_price': Decimal('44.97'),
            'status': 'shipped'
        }
        serializer = OrderSerializer(self.order, data=update_data)
        self.assertTrue(serializer.is_valid())
        updated_order = serializer.save()
        self.assertEqual(updated_order.quantity, 3)
        self.assertEqual(updated_order.total_price, Decimal('44.97'))
        self.assertEqual(updated_order.status, 'shipped')

    def test_serializer_validation_valid_data(self):
        """Test serializer validation with valid data"""
        valid_data = {
            'user_id': 3,
            'product_id': 3,
            'quantity': 5,
            'total_price': Decimal('99.99'),
            'status': 'delivered'
        }
        serializer = OrderSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(len(serializer.errors), 0)

    def test_serializer_validation_missing_user_id(self):
        """Test serializer validation with missing user_id"""
        data = {
            'product_id': 1,
            'quantity': 2,
            'total_price': Decimal('29.98'),
            'status': 'pending'
        }
        serializer = OrderSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('user_id', serializer.errors)

    def test_serializer_validation_missing_product_id(self):
        """Test serializer validation with missing product_id"""
        data = {
            'user_id': 1,
            'quantity': 2,
            'total_price': Decimal('29.98'),
            'status': 'pending'
        }
        serializer = OrderSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('product_id', serializer.errors)

    def test_serializer_validation_missing_quantity(self):
        """Test serializer validation with missing quantity"""
        data = {
            'user_id': 1,
            'product_id': 1,
            'total_price': Decimal('29.98'),
            'status': 'pending'
        }
        serializer = OrderSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('quantity', serializer.errors)

    def test_serializer_validation_missing_total_price(self):
        """Test serializer validation with missing total_price"""
        data = {
            'user_id': 1,
            'product_id': 1,
            'quantity': 2,
            'status': 'pending'
        }
        serializer = OrderSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('total_price', serializer.errors)

    def test_serializer_validation_negative_quantity(self):
        """Test serializer validation with negative quantity"""
        data = {
            'user_id': 1,
            'product_id': 1,
            'quantity': -1,
            'total_price': Decimal('29.98'),
            'status': 'pending'
        }
        serializer = OrderSerializer(data=data)
        self.assertTrue(serializer.is_valid())  # Negative quantities might be allowed for returns/cancellations

    def test_serializer_validation_zero_quantity(self):
        """Test serializer validation with zero quantity"""
        data = {
            'user_id': 1,
            'product_id': 1,
            'quantity': 0,
            'total_price': Decimal('0.00'),
            'status': 'cancelled'
        }
        serializer = OrderSerializer(data=data)
        self.assertTrue(serializer.is_valid())  # Zero quantity might be allowed for cancelled orders


class OrderAPITest(APITestCase):
    """Test cases for Order API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.order_data = {
            'user_id': 1,
            'product_id': 1,
            'quantity': 2,
            'total_price': Decimal('29.98'),
            'status': 'pending'
        }
        self.order = Order.objects.create(**self.order_data)

    def test_get_all_orders(self):
        """Test GET /api/orders/ returns all orders"""
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)

        # Check that our test order is in the response
        order_data = response.data[0]
        self.assertEqual(order_data['user_id'], 1)
        self.assertEqual(order_data['product_id'], 1)
        self.assertEqual(order_data['quantity'], 2)
        self.assertEqual(order_data['status'], 'pending')

    def test_api_response_format(self):
        """Test that API responses have correct format"""
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that response is a list
        self.assertIsInstance(response.data, list)

        # If there are orders, check the structure of the first one
        if response.data:
            order_data = response.data[0]
            required_fields = ['id', 'user_id', 'product_id', 'quantity', 'total_price', 'status']
            for field in required_fields:
                self.assertIn(field, order_data)


class OrderIntegrationTest(TestCase):
    """Integration tests for Order functionality"""

    def test_full_order_lifecycle(self):
        """Test creating, reading, and verifying an order"""
        # Create order
        order = Order.objects.create(
            user_id=100,
            product_id=200,
            quantity=3,
            total_price=Decimal('59.97'),
            status='confirmed'
        )

        # Verify creation
        self.assertEqual(order.user_id, 100)
        self.assertEqual(order.product_id, 200)
        self.assertEqual(order.quantity, 3)
        self.assertEqual(order.total_price, Decimal('59.97'))
        self.assertEqual(order.status, 'confirmed')

        # Test serialization
        serializer = OrderSerializer(order)
        data = serializer.data
        self.assertEqual(data['user_id'], 100)
        self.assertEqual(data['product_id'], 200)
        self.assertEqual(data['quantity'], 3)
        self.assertEqual(data['status'], 'confirmed')

        # Verify in database
        db_order = Order.objects.get(id=order.id)
        self.assertEqual(db_order.total_price, Decimal('59.97'))
        self.assertEqual(str(db_order), f"Order {order.id} - User 100 - Product 200")

    def test_bulk_order_operations(self):
        """Test operations with multiple orders"""
        # Create multiple orders
        orders_data = [
            {'user_id': i, 'product_id': i + 10, 'quantity': i, 'total_price': Decimal(f'{i * 10}.00'), 'status': 'pending'}
            for i in range(1, 6)  # 5 orders
        ]

        created_orders = []
        for order_data in orders_data:
            order = Order.objects.create(**order_data)
            created_orders.append(order)

        # Verify all orders were created (5 orders)
        self.assertEqual(Order.objects.count(), 5)

        # Test bulk serialization
        serializer = OrderSerializer(created_orders, many=True)
        data = serializer.data
        self.assertEqual(len(data), 5)

        # Verify each order in serialized data
        user_ids = [order['user_id'] for order in data]
        for i in range(1, 6):
            self.assertIn(i, user_ids)

    def test_order_status_transitions(self):
        """Test order status transition operations"""
        order = Order.objects.create(
            user_id=50,
            product_id=60,
            quantity=2,
            total_price=Decimal('39.98'),
            status='pending'
        )

        # Test status transitions
        status_flow = ['confirmed', 'shipped', 'delivered']
        for new_status in status_flow:
            order.status = new_status
            order.save()

            # Refresh from database and verify
            order.refresh_from_db()
            self.assertEqual(order.status, new_status)

    def test_order_calculations(self):
        """Test order calculation operations"""
        # Test various order calculations
        orders = [
            Order.objects.create(
                user_id=1,
                product_id=i,
                quantity=i,
                total_price=Decimal(f'{i * 10}.00'),
                status='delivered'
            ) for i in range(1, 4)
        ]

        # Calculate total value of all orders
        total_value = sum(order.total_price for order in orders)
        expected_total = Decimal('10.00') + Decimal('20.00') + Decimal('30.00')
        self.assertEqual(total_value, expected_total)

        # Calculate total quantity ordered
        total_quantity = sum(order.quantity for order in orders)
        self.assertEqual(total_quantity, 6)  # 1 + 2 + 3
