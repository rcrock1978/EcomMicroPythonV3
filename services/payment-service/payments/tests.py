from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
from .models import Payment
from .serializers import PaymentSerializer


class PaymentModelTest(TestCase):
    """Test cases for Payment model"""

    def setUp(self):
        """Set up test data"""
        self.payment = Payment.objects.create(
            order_id=1,
            amount=Decimal('99.99'),
            method='credit_card',
            status='pending',
            transaction_id='txn_123456'
        )

    def test_payment_creation(self):
        """Test that a payment can be created with valid data"""
        self.assertEqual(self.payment.order_id, 1)
        self.assertEqual(self.payment.amount, Decimal('99.99'))
        self.assertEqual(self.payment.method, 'credit_card')
        self.assertEqual(self.payment.status, 'pending')
        self.assertEqual(self.payment.transaction_id, 'txn_123456')
        self.assertIsNotNone(self.payment.id)
        self.assertIsNotNone(self.payment.created_at)

    def test_payment_str_method(self):
        """Test the string representation of Payment model"""
        expected_str = f"Payment {self.payment.id} - Order 1 - pending"
        self.assertEqual(str(self.payment), expected_str)

    def test_payment_field_constraints(self):
        """Test field constraints"""
        # Test method max length
        long_method = "a" * 50
        payment = Payment.objects.create(
            order_id=2,
            amount=Decimal('10.00'),
            method=long_method,
            status='completed'
        )
        self.assertEqual(len(payment.method), 50)

        # Test status max length
        long_status = "b" * 50
        payment2 = Payment.objects.create(
            order_id=3,
            amount=Decimal('20.00'),
            method='paypal',
            status=long_status
        )
        self.assertEqual(len(payment2.status), 50)

        # Test transaction_id max length
        long_txn_id = "c" * 255
        payment3 = Payment.objects.create(
            order_id=4,
            amount=Decimal('30.00'),
            method='bank_transfer',
            status='failed',
            transaction_id=long_txn_id
        )
        self.assertEqual(len(payment3.transaction_id), 255)

    def test_payment_default_values(self):
        """Test default field values"""
        payment = Payment.objects.create(
            order_id=5,
            amount=Decimal('15.00'),
            method='cash'
        )
        self.assertEqual(payment.status, 'pending')
        self.assertEqual(payment.transaction_id, '')

    def test_payment_status_choices(self):
        """Test payment status values"""
        # Test different status values
        statuses = ['pending', 'completed', 'failed', 'refunded', 'cancelled']
        for i, status_val in enumerate(statuses):
            payment = Payment.objects.create(
                order_id=10 + i,
                amount=Decimal('10.00'),
                method='credit_card',
                status=status_val
            )
            self.assertEqual(payment.status, status_val)

    def test_payment_method_choices(self):
        """Test payment method values"""
        # Test different payment methods
        methods = ['credit_card', 'debit_card', 'paypal', 'bank_transfer', 'cash', 'crypto']
        for i, method_val in enumerate(methods):
            payment = Payment.objects.create(
                order_id=20 + i,
                amount=Decimal('25.00'),
                method=method_val,
                status='completed'
            )
            self.assertEqual(payment.method, method_val)

    def test_payment_amount_precision(self):
        """Test payment amount decimal precision"""
        payment = Payment.objects.create(
            order_id=30,
            amount=Decimal('123.456789'),  # PostgreSQL stores full precision
            method='credit_card',
            status='completed'
        )
        # PostgreSQL stores the full decimal precision
        self.assertEqual(payment.amount, Decimal('123.456789'))


class PaymentSerializerTest(TestCase):
    """Test cases for Payment serializer"""

    def setUp(self):
        """Set up test data"""
        self.payment_data = {
            'order_id': 1,
            'amount': Decimal('99.99'),
            'method': 'credit_card',
            'status': 'pending',
            'transaction_id': 'txn_123456'
        }
        self.payment = Payment.objects.create(**self.payment_data)

    def test_serializer_contains_expected_fields(self):
        """Test that serializer contains all expected fields"""
        serializer = PaymentSerializer(self.payment)
        data = serializer.data
        expected_fields = ['id', 'order_id', 'amount', 'method', 'status', 'transaction_id', 'created_at']
        for field in expected_fields:
            self.assertIn(field, data)

    def test_serializer_data_types(self):
        """Test that serializer returns correct data types"""
        serializer = PaymentSerializer(self.payment)
        data = serializer.data
        self.assertIsInstance(data['id'], int)
        self.assertIsInstance(data['order_id'], int)
        self.assertIsInstance(data['amount'], str)  # Decimal is serialized as string
        self.assertIsInstance(data['method'], str)
        self.assertIsInstance(data['status'], str)
        self.assertIsInstance(data['transaction_id'], str)
        self.assertIsNotNone(data['created_at'])

    def test_serializer_create(self):
        """Test serializer create functionality"""
        create_data = {
            'order_id': 2,
            'amount': Decimal('149.99'),
            'method': 'paypal',
            'status': 'completed',
            'transaction_id': 'txn_789012'
        }
        serializer = PaymentSerializer(data=create_data)
        self.assertTrue(serializer.is_valid())
        payment = serializer.save()
        self.assertEqual(payment.order_id, 2)
        self.assertEqual(payment.amount, Decimal('149.99'))
        self.assertEqual(payment.method, 'paypal')
        self.assertEqual(payment.status, 'completed')
        self.assertEqual(payment.transaction_id, 'txn_789012')

    def test_serializer_update(self):
        """Test serializer update functionality"""
        update_data = {
            'order_id': 1,
            'amount': Decimal('199.99'),
            'method': 'credit_card',
            'status': 'completed',
            'transaction_id': 'txn_updated_123'
        }
        serializer = PaymentSerializer(self.payment, data=update_data)
        self.assertTrue(serializer.is_valid())
        updated_payment = serializer.save()
        self.assertEqual(updated_payment.amount, Decimal('199.99'))
        self.assertEqual(updated_payment.status, 'completed')
        self.assertEqual(updated_payment.transaction_id, 'txn_updated_123')

    def test_serializer_validation_valid_data(self):
        """Test serializer validation with valid data"""
        valid_data = {
            'order_id': 3,
            'amount': Decimal('79.99'),
            'method': 'bank_transfer',
            'status': 'failed',
            'transaction_id': 'txn_valid_456'
        }
        serializer = PaymentSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(len(serializer.errors), 0)

    def test_serializer_validation_missing_order_id(self):
        """Test serializer validation with missing order_id"""
        data = {
            'amount': Decimal('99.99'),
            'method': 'credit_card',
            'status': 'pending'
        }
        serializer = PaymentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('order_id', serializer.errors)

    def test_serializer_validation_missing_amount(self):
        """Test serializer validation with missing amount"""
        data = {
            'order_id': 1,
            'method': 'credit_card',
            'status': 'pending'
        }
        serializer = PaymentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('amount', serializer.errors)

    def test_serializer_validation_missing_method(self):
        """Test serializer validation with missing method"""
        data = {
            'order_id': 1,
            'amount': Decimal('99.99'),
            'status': 'pending'
        }
        serializer = PaymentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('method', serializer.errors)

    def test_serializer_validation_zero_amount(self):
        """Test serializer validation with zero amount"""
        data = {
            'order_id': 1,
            'amount': Decimal('0.00'),
            'method': 'credit_card',
            'status': 'completed'
        }
        serializer = PaymentSerializer(data=data)
        self.assertTrue(serializer.is_valid())  # Zero amount might be allowed for refunds

    def test_serializer_validation_negative_amount(self):
        """Test serializer validation with negative amount"""
        data = {
            'order_id': 1,
            'amount': Decimal('-50.00'),
            'method': 'credit_card',
            'status': 'refunded'
        }
        serializer = PaymentSerializer(data=data)
        self.assertTrue(serializer.is_valid())  # Negative amounts might be allowed for refunds

    def test_serializer_validation_blank_transaction_id(self):
        """Test serializer validation with blank transaction_id"""
        data = {
            'order_id': 1,
            'amount': Decimal('99.99'),
            'method': 'cash',
            'status': 'completed',
            'transaction_id': ''  # Blank should be allowed
        }
        serializer = PaymentSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class PaymentAPITest(APITestCase):
    """Test cases for Payment API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.payment_data = {
            'order_id': 1,
            'amount': Decimal('99.99'),
            'method': 'credit_card',
            'status': 'pending',
            'transaction_id': 'txn_123456'
        }
        self.payment = Payment.objects.create(**self.payment_data)

    def test_get_all_payments(self):
        """Test GET /api/payments/ returns all payments"""
        response = self.client.get('/api/payments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)

        # Check that our test payment is in the response
        payment_data = response.data[0]
        self.assertEqual(payment_data['order_id'], 1)
        self.assertEqual(payment_data['amount'], '99.99')
        self.assertEqual(payment_data['method'], 'credit_card')
        self.assertEqual(payment_data['status'], 'pending')
        self.assertEqual(payment_data['transaction_id'], 'txn_123456')

    def test_create_payment_valid_data(self):
        """Test POST /api/payments/ with valid data"""
        new_payment_data = {
            'order_id': 2,
            'amount': Decimal('149.99'),
            'method': 'paypal',
            'status': 'completed',
            'transaction_id': 'txn_789012'
        }
        response = self.client.post('/api/payments/', new_payment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check response data
        self.assertEqual(response.data['order_id'], 2)
        self.assertEqual(response.data['amount'], '149.99')
        self.assertEqual(response.data['method'], 'paypal')
        self.assertEqual(response.data['status'], 'completed')
        self.assertEqual(response.data['transaction_id'], 'txn_789012')

        # Check database
        payment = Payment.objects.get(order_id=2)
        self.assertEqual(payment.amount, Decimal('149.99'))
        self.assertEqual(payment.method, 'paypal')

    def test_create_payment_missing_fields(self):
        """Test POST /api/payments/ with missing required fields"""
        incomplete_data = {
            'order_id': 3,
            'amount': Decimal('79.99'),
            'method': 'bank_transfer'
            # Missing status (has default value)
        }
        response = self.client.post('/api/payments/', incomplete_data, format='json')
        # Status has a default value, so it should work
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_api_response_format(self):
        """Test that API responses have correct format"""
        response = self.client.get('/api/payments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that response is a list
        self.assertIsInstance(response.data, list)

        # If there are payments, check the structure of the first one
        if response.data:
            payment_data = response.data[0]
            required_fields = ['id', 'order_id', 'amount', 'method', 'status', 'transaction_id', 'created_at']
            for field in required_fields:
                self.assertIn(field, payment_data)


class PaymentIntegrationTest(TestCase):
    """Integration tests for Payment functionality"""

    def test_full_payment_lifecycle(self):
        """Test creating, reading, and verifying a payment"""
        # Create payment
        payment = Payment.objects.create(
            order_id=100,
            amount=Decimal('299.99'),
            method='credit_card',
            status='pending',
            transaction_id='txn_lifecycle_001'
        )

        # Verify creation
        self.assertEqual(payment.order_id, 100)
        self.assertEqual(payment.amount, Decimal('299.99'))
        self.assertEqual(payment.method, 'credit_card')
        self.assertEqual(payment.status, 'pending')
        self.assertEqual(payment.transaction_id, 'txn_lifecycle_001')

        # Test serialization
        serializer = PaymentSerializer(payment)
        data = serializer.data
        self.assertEqual(data['order_id'], 100)
        self.assertEqual(data['amount'], '299.99')
        self.assertEqual(data['method'], 'credit_card')
        self.assertEqual(data['status'], 'pending')

        # Verify in database
        db_payment = Payment.objects.get(order_id=100)
        self.assertEqual(db_payment.amount, Decimal('299.99'))
        self.assertEqual(str(db_payment), f"Payment {payment.id} - Order 100 - pending")

    def test_bulk_payment_operations(self):
        """Test operations with multiple payments"""
        # Create multiple payments
        payments_data = [
            {'order_id': i, 'amount': Decimal(f'{i * 10}.00'), 'method': 'credit_card', 'status': 'completed', 'transaction_id': f'txn_bulk_{i}'}
            for i in range(1, 6)  # 5 payments
        ]

        created_payments = []
        for payment_data in payments_data:
            payment = Payment.objects.create(**payment_data)
            created_payments.append(payment)

        # Verify all payments were created (5 payments)
        self.assertEqual(Payment.objects.count(), 5)

        # Test bulk serialization
        serializer = PaymentSerializer(created_payments, many=True)
        data = serializer.data
        self.assertEqual(len(data), 5)

        # Verify each payment in serialized data
        order_ids = [payment['order_id'] for payment in data]
        for i in range(1, 6):
            self.assertIn(i, order_ids)

    def test_payment_status_transitions(self):
        """Test payment status transition operations"""
        payment = Payment.objects.create(
            order_id=50,
            amount=Decimal('199.99'),
            method='paypal',
            status='pending',
            transaction_id='txn_status_test'
        )

        # Test status transitions
        status_flow = ['completed', 'refunded']
        for new_status in status_flow:
            payment.status = new_status
            payment.save()

            # Refresh from database and verify
            payment.refresh_from_db()
            self.assertEqual(payment.status, new_status)

    def test_payment_calculations(self):
        """Test payment calculation operations"""
        # Test various payment calculations
        payments = [
            Payment.objects.create(
                order_id=i,
                amount=Decimal(f'{i * 25}.00'),
                method='credit_card',
                status='completed',
                transaction_id=f'txn_calc_{i}'
            ) for i in range(1, 4)
        ]

        # Calculate total payment amount
        total_amount = sum(payment.amount for payment in payments)
        expected_total = Decimal('25.00') + Decimal('50.00') + Decimal('75.00')
        self.assertEqual(total_amount, expected_total)

        # Count payments by status
        completed_count = Payment.objects.filter(status='completed').count()
        self.assertEqual(completed_count, 3)

    def test_payment_method_distribution(self):
        """Test payment method distribution analysis"""
        # Create payments with different methods
        methods_and_counts = [
            ('credit_card', 3),
            ('paypal', 2),
            ('bank_transfer', 1),
            ('cash', 1)
        ]

        payment_id = 1
        for method, count in methods_and_counts:
            for _ in range(count):
                Payment.objects.create(
                    order_id=payment_id,
                    amount=Decimal('100.00'),
                    method=method,
                    status='completed',
                    transaction_id=f'txn_method_{payment_id}'
                )
                payment_id += 1

        # Verify method counts
        for method, expected_count in methods_and_counts:
            actual_count = Payment.objects.filter(method=method).count()
            self.assertEqual(actual_count, expected_count)
