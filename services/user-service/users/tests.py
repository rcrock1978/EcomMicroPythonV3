from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import User
from .serializers import UserSerializer


class UserModelTest(TestCase):
    """Test cases for User model"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )

    def test_user_creation(self):
        """Test that a user can be created with valid data"""
        self.assertEqual(self.user.username, "testuser")
        self.assertEqual(self.user.email, "test@example.com")
        self.assertEqual(self.user.password, "testpass123")
        self.assertEqual(self.user.first_name, "Test")
        self.assertEqual(self.user.last_name, "User")
        self.assertTrue(self.user.is_active)
        self.assertIsNotNone(self.user.id)
        self.assertIsNotNone(self.user.date_joined)

    def test_user_str_method(self):
        """Test the string representation of User model"""
        self.assertEqual(str(self.user), "testuser")

    def test_user_field_constraints(self):
        """Test field constraints and uniqueness"""
        # Test username max length
        long_username = "a" * 150
        user = User.objects.create(
            username=long_username,
            email="long@example.com",
            password="testpass123"
        )
        self.assertEqual(len(user.username), 150)

        # Test unique constraints
        with self.assertRaises(Exception):  # Should raise IntegrityError for duplicate username
            User.objects.create(
                username="testuser",  # Same as existing user
                email="different@example.com",
                password="testpass123"
            )

        with self.assertRaises(Exception):  # Should raise IntegrityError for duplicate email
            User.objects.create(
                username="differentuser",
                email="test@example.com",  # Same as existing user
                password="testpass123"
            )

    def test_user_default_values(self):
        """Test default field values"""
        user = User.objects.create(
            username="defaultuser",
            email="default@example.com",
            password="testpass123"
        )
        self.assertTrue(user.is_active)
        self.assertIsNotNone(user.date_joined)


class UserSerializerTest(TestCase):
    """Test cases for User serializer"""

    def setUp(self):
        """Set up test data"""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        self.user = User.objects.create(**self.user_data)

    def test_serializer_contains_expected_fields(self):
        """Test that serializer contains all expected fields"""
        serializer = UserSerializer(self.user)
        data = serializer.data
        expected_fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']
        for field in expected_fields:
            self.assertIn(field, data)
        # Password should not be in response data
        self.assertNotIn('password', data)

    def test_serializer_data_types(self):
        """Test that serializer returns correct data types"""
        serializer = UserSerializer(self.user)
        data = serializer.data
        self.assertIsInstance(data['id'], int)
        self.assertIsInstance(data['username'], str)
        self.assertIsInstance(data['email'], str)
        self.assertIsInstance(data['first_name'], str)
        self.assertIsInstance(data['last_name'], str)
        self.assertIsInstance(data['is_active'], bool)
        self.assertIsNotNone(data['date_joined'])

    def test_serializer_create(self):
        """Test serializer create functionality"""
        create_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        serializer = UserSerializer(data=create_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'new@example.com')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'User')

    def test_serializer_update(self):
        """Test serializer update functionality"""
        update_data = {
            'username': 'updateduser',
            'email': 'updated@example.com',
            'first_name': 'Updated',
            'last_name': 'User',
            'is_active': False
        }
        serializer = UserSerializer(self.user, data=update_data)
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        self.assertEqual(updated_user.username, 'updateduser')
        self.assertEqual(updated_user.email, 'updated@example.com')
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.last_name, 'User')
        self.assertFalse(updated_user.is_active)

    def test_serializer_validation_valid_data(self):
        """Test serializer validation with valid data"""
        valid_data = {
            'username': 'validuser',
            'email': 'valid@example.com',
            'password': 'validpass123',
            'first_name': 'Valid',
            'last_name': 'User'
        }
        serializer = UserSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(len(serializer.errors), 0)

    def test_serializer_validation_missing_username(self):
        """Test serializer validation with missing username"""
        data = self.user_data.copy()
        del data['username']
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)

    def test_serializer_validation_missing_email(self):
        """Test serializer validation with missing email"""
        data = self.user_data.copy()
        del data['email']
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_serializer_validation_invalid_email(self):
        """Test serializer validation with invalid email"""
        data = self.user_data.copy()
        data['email'] = 'invalid-email'
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_serializer_validation_duplicate_username(self):
        """Test serializer validation with duplicate username"""
        # Create first user
        User.objects.create(
            username='existinguser',
            email='existing@example.com',
            password='testpass123'
        )

        # Try to create second user with same username
        data = self.user_data.copy()
        data['username'] = 'existinguser'
        data['email'] = 'different@example.com'
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)

    def test_serializer_validation_duplicate_email(self):
        """Test serializer validation with duplicate email"""
        # Create first user
        User.objects.create(
            username='existinguser',
            email='existing@example.com',
            password='testpass123'
        )

        # Try to create second user with same email
        data = self.user_data.copy()
        data['username'] = 'differentuser'
        data['email'] = 'existing@example.com'
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)


class UserAPITest(APITestCase):
    """Test cases for User API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        self.user = User.objects.create(**self.user_data)

    def test_get_all_users(self):
        """Test GET /api/users/ returns all users"""
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)

        # Check that our test user is in the response
        user_data = response.data[0]
        self.assertEqual(user_data['username'], 'testuser')
        self.assertEqual(user_data['email'], 'test@example.com')
        self.assertEqual(user_data['first_name'], 'Test')
        self.assertEqual(user_data['last_name'], 'User')
        self.assertTrue(user_data['is_active'])
        self.assertNotIn('password', user_data)  # Password should not be in response

    def test_create_user_valid_data(self):
        """Test POST /api/users/ with valid data"""
        new_user_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post('/api/users/', new_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check response data
        self.assertEqual(response.data['username'], 'newuser')
        self.assertEqual(response.data['email'], 'new@example.com')
        self.assertEqual(response.data['first_name'], 'New')
        self.assertEqual(response.data['last_name'], 'User')
        self.assertTrue(response.data['is_active'])
        self.assertNotIn('password', response.data)

        # Check database
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'new@example.com')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'User')

    def test_create_user_missing_fields(self):
        """Test POST /api/users/ with missing required fields"""
        incomplete_data = {
            'username': 'incompleteuser',
            # Missing email and password
            'first_name': 'Incomplete'
        }
        response = self.client.post('/api/users/', incomplete_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        # Password is write_only so it won't appear in error response

    def test_create_user_invalid_data(self):
        """Test POST /api/users/ with invalid data"""
        invalid_data = {
            'username': 'invaliduser',
            'email': 'invalid-email',  # Invalid email format
            'password': 'pass',
            'first_name': 'Invalid'
        }
        response = self.client.post('/api/users/', invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_create_user_duplicate_username(self):
        """Test POST /api/users/ with duplicate username"""
        duplicate_data = {
            'username': 'testuser',  # Same as existing user
            'email': 'different@example.com',
            'password': 'newpass123'
        }
        response = self.client.post('/api/users/', duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_create_user_duplicate_email(self):
        """Test POST /api/users/ with duplicate email"""
        duplicate_data = {
            'username': 'differentuser',
            'email': 'test@example.com',  # Same as existing user
            'password': 'newpass123'
        }
        response = self.client.post('/api/users/', duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_api_response_format(self):
        """Test that API responses have correct format"""
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that response is a list
        self.assertIsInstance(response.data, list)

        # If there are users, check the structure of the first one
        if response.data:
            user_data = response.data[0]
            required_fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']
            for field in required_fields:
                self.assertIn(field, user_data)


class UserIntegrationTest(TestCase):
    """Integration tests for User functionality"""

    def test_full_user_lifecycle(self):
        """Test creating, reading, and verifying a user"""
        # Create user
        user = User.objects.create(
            username='lifecycleuser',
            email='lifecycle@example.com',
            password='lifepass123',
            first_name='Life',
            last_name='Cycle'
        )

        # Verify creation
        self.assertEqual(user.username, 'lifecycleuser')
        self.assertEqual(user.email, 'lifecycle@example.com')
        self.assertTrue(user.is_active)

        # Test serialization
        serializer = UserSerializer(user)
        data = serializer.data
        self.assertEqual(data['username'], 'lifecycleuser')
        self.assertEqual(data['email'], 'lifecycle@example.com')
        self.assertNotIn('password', data)

        # Verify in database
        db_user = User.objects.get(username='lifecycleuser')
        self.assertEqual(db_user.email, 'lifecycle@example.com')
        self.assertEqual(str(db_user), 'lifecycleuser')

    def test_bulk_user_operations(self):
        """Test operations with multiple users"""
        # Create multiple users
        users_data = [
            {'username': f'bulkuser{i}', 'email': f'bulk{i}@example.com', 'password': 'bulkpass123'}
            for i in range(5)
        ]

        created_users = []
        for user_data in users_data:
            user = User.objects.create(**user_data)
            created_users.append(user)

        # Verify all users were created (5 new users)
        self.assertEqual(User.objects.count(), 5)

        # Test bulk serialization
        serializer = UserSerializer(created_users, many=True)
        data = serializer.data
        self.assertEqual(len(data), 5)

        # Verify each user in serialized data
        usernames = [user['username'] for user in data]
        for i in range(5):
            self.assertIn(f'bulkuser{i}', usernames)
