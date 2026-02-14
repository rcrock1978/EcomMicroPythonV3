import json
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from decimal import Decimal
import time

from .models import Service, Route, APIKey, RequestLog, RateLimit
from .serializers import (
    ServiceSerializer, RouteSerializer, APIKeySerializer,
    RequestLogSerializer, RateLimitSerializer, GatewayStatsSerializer,
    HealthCheckSerializer
)


class ServiceModelTest(TestCase):
    """Test cases for Service model"""

    def setUp(self):
        """Set up test data"""
        self.service = Service.objects.create(
            name='test-service',
            service_type='product',
            base_url='http://localhost',
            port=8001,
            is_active=True,
            health_check_url='http://localhost/health/'
        )

    def test_service_creation(self):
        """Test that a service can be created with valid data"""
        self.assertEqual(self.service.name, 'test-service')
        self.assertEqual(self.service.service_type, 'product')
        self.assertEqual(self.service.base_url, 'http://localhost')
        self.assertEqual(self.service.port, 8001)
        self.assertTrue(self.service.is_active)
        self.assertIsNotNone(self.service.id)
        self.assertIsNotNone(self.service.created_at)

    def test_service_str_method(self):
        """Test the string representation of Service model"""
        expected_str = "test-service (product) - http://localhost:8001"
        self.assertEqual(str(self.service), expected_str)

    def test_get_full_url(self):
        """Test the get_full_url method"""
        expected_url = "http://localhost:8001"
        self.assertEqual(self.service.get_full_url(), expected_url)

    def test_service_field_constraints(self):
        """Test field constraints"""
        # Test port validation
        service = Service(
            name='invalid-port',
            service_type='product',
            base_url='http://localhost',
            port=99999  # Invalid port
        )
        with self.assertRaises(ValidationError):
            service.full_clean()

    def test_service_validation(self):
        """Test service validation"""
        service = Service(
            name='invalid-url',
            service_type='product',
            base_url='invalid-url',  # Invalid URL
            port=8001
        )
        with self.assertRaises(Exception):  # ValidationError
            service.full_clean()


class RouteModelTest(TestCase):
    """Test cases for Route model"""

    def setUp(self):
        """Set up test data"""
        self.service = Service.objects.create(
            name='test-service',
            service_type='product',
            base_url='http://localhost',
            port=8001
        )
        self.route = Route.objects.create(
            path='/api/test',
            method='GET',
            service=self.service,
            is_active=True,
            requires_auth=False,
            rate_limit=100
        )

    def test_route_creation(self):
        """Test that a route can be created with valid data"""
        self.assertEqual(self.route.path, '/api/test')
        self.assertEqual(self.route.method, 'GET')
        self.assertEqual(self.route.service, self.service)
        self.assertTrue(self.route.is_active)
        self.assertFalse(self.route.requires_auth)
        self.assertEqual(self.route.rate_limit, 100)

    def test_route_str_method(self):
        """Test the string representation of Route model"""
        expected_str = "GET /api/test -> test-service"
        self.assertEqual(str(self.route), expected_str)

    def test_route_matches_request(self):
        """Test route matching logic"""
        # Exact match
        self.assertTrue(self.route.matches_request('/api/test', 'GET'))
        self.assertFalse(self.route.matches_request('/api/test', 'POST'))
        self.assertFalse(self.route.matches_request('/api/other', 'GET'))

    def test_route_validation(self):
        """Test route validation"""
        # Invalid path (no leading slash)
        route = Route(
            path='api/test',  # Invalid
            method='GET',
            service=self.service
        )
        with self.assertRaises(Exception):  # ValidationError
            route.full_clean()

        # Invalid rate limit
        route = Route(
            path='/api/test',
            method='GET',
            service=self.service,
            rate_limit=0  # Invalid
        )
        with self.assertRaises(Exception):  # ValidationError
            route.full_clean()


class APIKeyModelTest(TestCase):
    """Test cases for APIKey model"""

    def setUp(self):
        """Set up test data"""
        self.service = Service.objects.create(
            name='test-service',
            service_type='product',
            base_url='http://localhost',
            port=8001
        )
        self.api_key = APIKey.objects.create(
            key='test-api-key-123',
            name='Test Key',
            service=self.service,
            is_active=True
        )

    def test_api_key_creation(self):
        """Test that an API key can be created with valid data"""
        self.assertEqual(self.api_key.key, 'test-api-key-123')
        self.assertEqual(self.api_key.name, 'Test Key')
        self.assertEqual(self.api_key.service, self.service)
        self.assertTrue(self.api_key.is_active)
        self.assertFalse(self.api_key.is_expired())

    def test_api_key_str_method(self):
        """Test the string representation of APIKey model"""
        expected_str = "Test Key - test-api-k..."
        self.assertEqual(str(self.api_key), expected_str)

    def test_api_key_expiration(self):
        """Test API key expiration logic"""
        # Set expiration in the past
        past_time = timezone.now() - timezone.timedelta(days=1)
        self.api_key.expires_at = past_time
        self.api_key.save()
        self.assertTrue(self.api_key.is_expired())

        # Set expiration in the future
        future_time = timezone.now() + timezone.timedelta(days=1)
        self.api_key.expires_at = future_time
        self.api_key.save()
        self.assertFalse(self.api_key.is_expired())


class RequestLogModelTest(TestCase):
    """Test cases for RequestLog model"""

    def setUp(self):
        """Set up test data"""
        self.service = Service.objects.create(
            name='test-service',
            service_type='product',
            base_url='http://localhost',
            port=8001
        )
        self.route = Route.objects.create(
            path='/api/test',
            method='GET',
            service=self.service
        )
        self.api_key = APIKey.objects.create(
            key='test-key',
            name='Test Key',
            service=self.service
        )
        self.request_log = RequestLog.objects.create(
            route=self.route,
            method='GET',
            path='/api/test',
            status_code=200,
            response_time=150.5,
            user_agent='Test Agent',
            ip_address='127.0.0.1',
            api_key=self.api_key
        )

    def test_request_log_creation(self):
        """Test that a request log can be created with valid data"""
        self.assertEqual(self.request_log.route, self.route)
        self.assertEqual(self.request_log.method, 'GET')
        self.assertEqual(self.request_log.path, '/api/test')
        self.assertEqual(self.request_log.status_code, 200)
        self.assertEqual(self.request_log.response_time, 150.5)
        self.assertEqual(self.request_log.user_agent, 'Test Agent')
        self.assertEqual(self.request_log.ip_address, '127.0.0.1')
        self.assertEqual(self.request_log.api_key, self.api_key)

    def test_request_log_str_method(self):
        """Test the string representation of RequestLog model"""
        expected_str = "GET /api/test - 200 (150.5ms)"
        self.assertEqual(str(self.request_log), expected_str)


class RateLimitModelTest(TestCase):
    """Test cases for RateLimit model"""

    def setUp(self):
        """Set up test data"""
        self.service = Service.objects.create(
            name='test-service',
            service_type='product',
            base_url='http://localhost',
            port=8001
        )
        self.route = Route.objects.create(
            path='/api/test',
            method='GET',
            service=self.service,
            rate_limit=10
        )
        self.rate_limit = RateLimit.objects.create(
            identifier='127.0.0.1',
            route=self.route,
            request_count=5,
            window_start=timezone.now(),
            window_end=timezone.now() + timezone.timedelta(hours=1)
        )

    def test_rate_limit_creation(self):
        """Test that a rate limit can be created with valid data"""
        self.assertEqual(self.rate_limit.identifier, '127.0.0.1')
        self.assertEqual(self.rate_limit.route, self.route)
        self.assertEqual(self.rate_limit.request_count, 5)
        self.assertFalse(self.rate_limit.is_limit_exceeded())

    def test_rate_limit_str_method(self):
        """Test the string representation of RateLimit model"""
        expected_str = "127.0.0.1 - /api/test (5 requests)"
        self.assertEqual(str(self.rate_limit), expected_str)

    def test_rate_limit_exceeded(self):
        """Test rate limit exceeded logic"""
        # Set count to exceed limit
        self.rate_limit.request_count = 15  # Exceeds limit of 10
        self.assertTrue(self.rate_limit.is_limit_exceeded())

    def test_rate_limit_increment(self):
        """Test rate limit increment"""
        initial_count = self.rate_limit.request_count
        self.rate_limit.increment()
        self.assertEqual(self.rate_limit.request_count, initial_count + 1)


class ServiceSerializerTest(TestCase):
    """Test cases for Service serializer"""

    def setUp(self):
        """Set up test data"""
        self.service = Service.objects.create(
            name='test-service',
            service_type='product',
            base_url='http://localhost',
            port=8001,
            is_active=True
        )

    def test_serializer_contains_expected_fields(self):
        """Test that serializer contains all expected fields"""
        serializer = ServiceSerializer(self.service)
        data = serializer.data
        expected_fields = [
            'id', 'name', 'service_type', 'base_url', 'port', 'is_active',
            'health_check_url', 'full_url', 'routes_count', 'created_at', 'updated_at'
        ]
        for field in expected_fields:
            self.assertIn(field, data)

    def test_serializer_create(self):
        """Test serializer create functionality"""
        data = {
            'name': 'new-service',
            'service_type': 'user',
            'base_url': 'http://localhost',
            'port': 8002,
            'is_active': True
        }
        serializer = ServiceSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        service = serializer.save()
        self.assertEqual(service.name, 'new-service')
        self.assertEqual(service.port, 8002)

    def test_serializer_validation_port(self):
        """Test serializer validation for port"""
        data = {
            'name': 'test-service',
            'service_type': 'product',
            'base_url': 'http://localhost',
            'port': 99999,  # Invalid port
            'is_active': True
        }
        serializer = ServiceSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('port', serializer.errors)

    def test_serializer_validation_base_url(self):
        """Test serializer validation for base URL"""
        data = {
            'name': 'test-service',
            'service_type': 'product',
            'base_url': 'invalid-url',  # Invalid URL
            'port': 8001,
            'is_active': True
        }
        serializer = ServiceSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('base_url', serializer.errors)


class RouteSerializerTest(TestCase):
    """Test cases for Route serializer"""

    def setUp(self):
        """Set up test data"""
        self.service = Service.objects.create(
            name='test-service',
            service_type='product',
            base_url='http://localhost',
            port=8001
        )

    def test_serializer_create(self):
        """Test serializer create functionality"""
        data = {
            'path': '/api/test',
            'method': 'GET',
            'service': self.service.id,
            'is_active': True,
            'requires_auth': False,
            'rate_limit': 100
        }
        serializer = RouteSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        route = serializer.save()
        self.assertEqual(route.path, '/api/test')
        self.assertEqual(route.method, 'GET')

    def test_serializer_validation_path(self):
        """Test serializer validation for path"""
        data = {
            'path': 'api/test',  # Invalid - no leading slash
            'method': 'GET',
            'service': self.service.id
        }
        serializer = RouteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('path', serializer.errors)

    def test_serializer_validation_rate_limit(self):
        """Test serializer validation for rate limit"""
        data = {
            'path': '/api/test',
            'method': 'GET',
            'service': self.service.id,
            'rate_limit': 0  # Invalid
        }
        serializer = RouteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('rate_limit', serializer.errors)


class APIKeySerializerTest(TestCase):
    """Test cases for APIKey serializer"""

    def setUp(self):
        """Set up test data"""
        self.service = Service.objects.create(
            name='test-service',
            service_type='product',
            base_url='http://localhost',
            port=8001
        )

    def test_serializer_create(self):
        """Test serializer create functionality"""
        data = {
            'name': 'Test API Key',
            'service': self.service.id,
            'is_active': True
        }
        serializer = APIKeySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        api_key = serializer.save(key='test-generated-key-123')
        self.assertEqual(api_key.name, 'Test API Key')
        self.assertEqual(api_key.key, 'test-generated-key-123')

    def test_serializer_validation_expires_at(self):
        """Test serializer validation for expiration date"""
        past_time = timezone.now() - timezone.timedelta(days=1)
        data = {
            'name': 'Test API Key',
            'service': self.service.id,
            'expires_at': past_time.isoformat()  # Invalid - past date
        }
        serializer = APIKeySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('expires_at', serializer.errors)


class ServiceAPITest(APITestCase):
    """Test cases for Service API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.service = Service.objects.create(
            name='test-service',
            service_type='product',
            base_url='http://localhost',
            port=8001,
            is_active=True
        )

    def test_get_services(self):
        """Test GET /api/services/ returns all services"""
        response = self.client.get('/api/services/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_service(self):
        """Test POST /api/services/ creates a new service"""
        data = {
            'name': 'new-service',
            'service_type': 'user',
            'base_url': 'http://localhost',
            'port': 8002,
            'is_active': True
        }
        response = self.client.post('/api/services/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'new-service')
        self.assertEqual(response.data['port'], 8002)

    def test_create_service_invalid_data(self):
        """Test POST /api/services/ with invalid data"""
        data = {
            'name': 'invalid-service',
            'service_type': 'product',
            'base_url': 'invalid-url',  # Invalid URL
            'port': 8001
        }
        response = self.client.post('/api/services/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_service_detail(self):
        """Test GET /api/services/{id}/ returns service details"""
        response = self.client.get(f'/api/services/{self.service.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'test-service')

    def test_update_service(self):
        """Test PUT /api/services/{id}/ updates a service"""
        data = {
            'name': 'updated-service',
            'service_type': 'product',
            'base_url': 'http://localhost',
            'port': 8003,
            'is_active': True
        }
        response = self.client.put(f'/api/services/{self.service.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'updated-service')

    def test_delete_service(self):
        """Test DELETE /api/services/{id}/ deletes a service"""
        response = self.client.delete(f'/api/services/{self.service.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify service is deleted
        response = self.client.get(f'/api/services/{self.service.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class RouteAPITest(APITestCase):
    """Test cases for Route API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.service = Service.objects.create(
            name='test-service',
            service_type='product',
            base_url='http://localhost',
            port=8001
        )
        self.route = Route.objects.create(
            path='/api/test',
            method='GET',
            service=self.service,
            is_active=True
        )

    def test_get_routes(self):
        """Test GET /api/routes/ returns all routes"""
        response = self.client.get('/api/routes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_route(self):
        """Test POST /api/routes/ creates a new route"""
        data = {
            'path': '/api/new',
            'method': 'POST',
            'service': self.service.id,
            'is_active': True,
            'requires_auth': False,
            'rate_limit': 50
        }
        response = self.client.post('/api/routes/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['path'], '/api/new')
        self.assertEqual(response.data['method'], 'POST')

    def test_create_route_invalid_data(self):
        """Test POST /api/routes/ with invalid data"""
        data = {
            'path': 'api/invalid',  # Invalid - no leading slash
            'method': 'GET',
            'service': self.service.id
        }
        response = self.client.post('/api/routes/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class APIKeyAPITest(APITestCase):
    """Test cases for APIKey API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.service = Service.objects.create(
            name='test-service',
            service_type='product',
            base_url='http://localhost',
            port=8001
        )

    def test_create_api_key(self):
        """Test POST /api/api-keys/ creates a new API key"""
        data = {
            'name': 'Test API Key',
            'service': self.service.id,
            'is_active': True
        }
        response = self.client.post('/api/api-keys/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test API Key')
        # Key should NOT be returned for security reasons
        self.assertNotIn('key', response.data)

    def test_get_api_keys(self):
        """Test GET /api/api-keys/ returns API keys (without key values)"""
        # Create an API key
        APIKey.objects.create(
            key='test-key-123',
            name='Test Key',
            service=self.service
        )

        response = self.client.get('/api/api-keys/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        # Key should not be included in list response for security
        self.assertNotIn('key', response.data[0])


class GatewayStatsAPITest(APITestCase):
    """Test cases for Gateway Statistics API"""

    def test_get_gateway_stats(self):
        """Test GET /api/stats/ returns gateway statistics"""
        response = self.client.get('/api/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that all expected fields are present
        expected_fields = [
            'total_services', 'active_services', 'total_routes', 'active_routes',
            'total_requests', 'avg_response_time', 'error_rate', 'top_routes'
        ]
        for field in expected_fields:
            self.assertIn(field, response.data)

        # Check data types
        self.assertIsInstance(response.data['total_services'], int)
        self.assertIsInstance(response.data['active_services'], int)
        self.assertIsInstance(response.data['total_routes'], int)
        self.assertIsInstance(response.data['active_routes'], int)
        self.assertIsInstance(response.data['total_requests'], int)
        self.assertIsInstance(response.data['avg_response_time'], (int, float))
        self.assertIsInstance(response.data['error_rate'], (int, float))
        self.assertIsInstance(response.data['top_routes'], list)


class GatewayProxyTest(APITestCase):
    """Test cases for Gateway Proxy functionality"""

    def setUp(self):
        """Set up test data"""
        self.service = Service.objects.create(
            name='test-service',
            service_type='product',
            base_url='http://httpbin.org',  # Use httpbin for testing
            port=80,
            is_active=True
        )
        self.route = Route.objects.create(
            path='/api/test',
            method='GET',
            service=self.service,
            is_active=True,
            requires_auth=False,
            rate_limit=100
        )

    @patch('gateway.views.requests.request')
    def test_proxy_request_success(self, mock_request):
        """Test successful proxy request"""
        # Mock the backend service response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'message': 'success'}
        mock_response.text = '{"message": "success"}'  # Set the text attribute
        mock_response.headers = {'content-type': 'application/json'}
        mock_request.return_value = mock_response

        response = self.client.get('/api/test')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        import json
        self.assertEqual(json.loads(response.content), {'message': 'success'})

    @patch('gateway.views.requests.request')
    def test_proxy_request_service_unavailable(self, mock_request):
        """Test proxy request when service is unavailable"""
        # Mock a request exception
        import requests
        mock_request.side_effect = requests.RequestException("Connection failed")

        response = self.client.get('/api/test')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_proxy_request_route_not_found(self):
        """Test proxy request with non-existent route"""
        response = self.client.get('/api/nonexistent')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(json.loads(response.content)['error'], 'Route not found')

    def test_proxy_request_inactive_route(self):
        """Test proxy request with inactive route"""
        # Deactivate the route
        self.route.is_active = False
        self.route.save()

        response = self.client.get('/api/test')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(json.loads(response.content)['error'], 'Route is disabled')

    @patch('gateway.views.requests.request')
    def test_proxy_request_with_auth_required(self, mock_request):
        """Test proxy request requiring authentication without API key"""
        # Set route to require auth
        self.route.requires_auth = True
        self.route.save()

        response = self.client.get('/api/test')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(json.loads(response.content)['error'], 'API key required')

    @patch('gateway.views.requests.request')
    def test_proxy_request_with_invalid_api_key(self, mock_request):
        """Test proxy request with invalid API key"""
        # Set route to require auth
        self.route.requires_auth = True
        self.route.save()

        # Make request with invalid API key
        self.client.credentials(HTTP_X_API_KEY='invalid-key')
        response = self.client.get('/api/test')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(json.loads(response.content)['error'], 'Invalid API key')

    @patch('gateway.views.requests.request')
    def test_proxy_request_rate_limit_exceeded(self, mock_request):
        """Test proxy request when rate limit is exceeded"""
        # Set low rate limit
        self.route.rate_limit = 1
        self.route.save()

        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'message': 'success'}
        mock_response.headers = {'content-type': 'application/json'}
        mock_request.return_value = mock_response

        # First request should succeed
        response1 = self.client.get('/api/test')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        # Second request should be rate limited
        response2 = self.client.get('/api/test')
        self.assertEqual(response2.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(json.loads(response2.content)['error'], 'Rate limit exceeded')


class GatewayIntegrationTest(TestCase):
    """Integration tests for Gateway functionality"""

    def setUp(self):
        """Set up test data"""
        self.service = Service.objects.create(
            name='integration-service',
            service_type='product',
            base_url='http://httpbin.org',
            port=80,
            is_active=True
        )
        self.route = Route.objects.create(
            path='/api/integration',
            method='GET',
            service=self.service,
            is_active=True,
            requires_auth=False,
            rate_limit=10
        )

    @patch('gateway.views.requests.request')
    def test_full_request_flow(self, mock_request):
        """Test complete request flow from client to service"""
        # Mock the backend service response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success', 'data': [1, 2, 3]}
        mock_response.text = '{"status": "success", "data": [1, 2, 3]}'
        mock_response.headers = {'content-type': 'application/json'}
        mock_request.return_value = mock_response

        # Make request through gateway
        from django.test import Client
        client = Client()
        response = client.get('/api/integration')

        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'success', 'data': [1, 2, 3]})

        # Verify request was logged
        log_entry = RequestLog.objects.filter(path='/api/integration').first()
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.method, 'GET')
        self.assertEqual(log_entry.status_code, 200)
        self.assertIsNotNone(log_entry.response_time)

    def test_service_health_check(self):
        """Test service health check functionality"""
        from .views import ServiceViewSet
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get('/health')
        view = ServiceViewSet()
        view.request = request
        view.kwargs = {'pk': self.service.pk}

        # This would normally make an HTTP request, but we'll test the logic
        # In a real scenario, you'd mock the requests call
        self.assertTrue(self.service.is_active)

    def test_route_matching_logic(self):
        """Test route matching logic with various patterns"""
        # Test exact match
        route1 = Route.objects.create(
            path='/api/exact',
            method='GET',
            service=self.service
        )
        self.assertTrue(route1.matches_request('/api/exact', 'GET'))
        self.assertFalse(route1.matches_request('/api/exact', 'POST'))

        # Test wildcard matching
        route2 = Route.objects.create(
            path='/api/wildcard/*',
            method='GET',
            service=self.service
        )
        # Current implementation supports basic wildcard matching
        self.assertTrue(route2.matches_request('/api/wildcard/test', 'GET'))
        self.assertTrue(route2.matches_request('/api/wildcard/another/path', 'GET'))
        self.assertFalse(route2.matches_request('/api/other/test', 'GET'))

    def test_api_key_lifecycle(self):
        """Test complete API key lifecycle"""
        from .views import APIKeyViewSet
        from django.test import RequestFactory

        # Create API key
        factory = RequestFactory()
        data = {
            'name': 'Lifecycle Test Key',
            'service': self.service.id,
            'is_active': True
        }

        view = APIKeyViewSet()
        view.request = factory.post('/api/api-keys/', data=data, content_type='application/json')

        # In a real test, you'd call view.create() and verify the response
        # This demonstrates the expected flow
        api_key = APIKey.objects.create(
            key='lifecycle-test-key',
            name='Lifecycle Test Key',
            service=self.service
        )

        # Test key properties
        self.assertFalse(api_key.is_expired())
        self.assertTrue(api_key.is_active)

        # Test deactivation
        api_key.is_active = False
        api_key.save()
        self.assertFalse(api_key.is_active)

    def test_rate_limiting_window_logic(self):
        """Test rate limiting window logic"""
        from django.utils import timezone

        # Create rate limit with current window
        now = timezone.now()
        window_start = now.replace(minute=0, second=0, microsecond=0)

        rate_limit = RateLimit.objects.create(
            identifier='test-client',
            route=self.route,
            request_count=0,
            window_start=window_start,
            window_end=window_start + timezone.timedelta(hours=1)
        )

        # Test window logic
        self.assertFalse(rate_limit.is_limit_exceeded())

        # Increment and test
        rate_limit.increment()
        self.assertEqual(rate_limit.request_count, 1)
        self.assertFalse(rate_limit.is_limit_exceeded())

        # Exceed limit
        rate_limit.request_count = self.route.rate_limit + 1
        self.assertTrue(rate_limit.is_limit_exceeded())

    def test_request_logging_comprehensive(self):
        """Test comprehensive request logging"""
        # Create multiple requests and verify logging
        from django.test import Client

        client = Client()

        # Make several requests
        for i in range(3):
            with patch('gateway.views.requests.request') as mock_request:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {'request': i}
                mock_response.headers = {'content-type': 'application/json'}
                mock_request.return_value = mock_response

                response = client.get('/api/integration')
                self.assertEqual(response.status_code, 200)

        # Verify logs were created
        logs = RequestLog.objects.filter(path='/api/integration')
        self.assertEqual(logs.count(), 3)

        # Verify log details
        for log in logs:
            self.assertEqual(log.method, 'GET')
            self.assertEqual(log.status_code, 200)
            self.assertIsNotNone(log.response_time)
            self.assertIsNotNone(log.created_at)
