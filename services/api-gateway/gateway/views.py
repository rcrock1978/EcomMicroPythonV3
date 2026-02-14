import requests
import time
import logging
import json
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from .models import Service, Route, APIKey, RequestLog, RateLimit
from .serializers import (
    ServiceSerializer, RouteSerializer, APIKeySerializer,
    RequestLogSerializer, RateLimitSerializer, GatewayStatsSerializer,
    HealthCheckSerializer
)

logger = logging.getLogger(__name__)


class ServiceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing services"""

    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = Service.objects.all()
        service_type = self.request.query_params.get('type', None)
        is_active = self.request.query_params.get('active', None)

        if service_type:
            queryset = queryset.filter(service_type=service_type)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset

    @action(detail=True, methods=['get'])
    def health(self, request, pk=None):
        """Check health of a specific service"""
        service = self.get_object()
        start_time = time.time()

        try:
            if service.health_check_url:
                response = requests.get(service.health_check_url, timeout=5)
                response_time = (time.time() - start_time) * 1000
                health_status = 'healthy' if response.status_code == 200 else 'unhealthy'
            else:
                # Basic connectivity check
                full_url = service.get_full_url()
                response = requests.get(f"{full_url}/health/", timeout=5)
                response_time = (time.time() - start_time) * 1000
                health_status = 'healthy' if response.status_code == 200 else 'unhealthy'
        except requests.RequestException:
            response_time = (time.time() - start_time) * 1000
            health_status = 'unreachable'

        serializer = HealthCheckSerializer({
            'service': service.name,
            'status': health_status,
            'response_time': round(response_time, 2),
            'timestamp': timezone.now()
        })

        return Response(serializer.data)


class RouteViewSet(viewsets.ModelViewSet):
    """ViewSet for managing routes"""

    queryset = Route.objects.all()
    serializer_class = RouteSerializer

    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = Route.objects.select_related('service')
        service_id = self.request.query_params.get('service', None)
        is_active = self.request.query_params.get('active', None)
        method = self.request.query_params.get('method', None)

        if service_id:
            queryset = queryset.filter(service_id=service_id)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if method:
            queryset = queryset.filter(method=method.upper())

        return queryset


class APIKeyViewSet(viewsets.ModelViewSet):
    """ViewSet for managing API keys"""

    queryset = APIKey.objects.all()
    serializer_class = APIKeySerializer

    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = APIKey.objects.select_related('service')
        service_id = self.request.query_params.get('service', None)
        is_active = self.request.query_params.get('active', None)
        is_expired = self.request.query_params.get('expired', None)

        if service_id:
            queryset = queryset.filter(service_id=service_id)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if is_expired is not None:
            # Filter expired keys
            now = timezone.now()
            if is_expired.lower() == 'true':
                queryset = queryset.filter(expires_at__lte=now)
            else:
                queryset = queryset.filter(
                    models.Q(expires_at__gt=now) | models.Q(expires_at__isnull=True)
                )

        return queryset

    def perform_create(self, serializer):
        """Generate API key on creation"""
        import secrets
        api_key = secrets.token_urlsafe(32)
        serializer.save(key=api_key)


class RequestLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing request logs"""

    queryset = RequestLog.objects.select_related('route', 'api_key')
    serializer_class = RequestLogSerializer

    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = RequestLog.objects.select_related('route', 'api_key')
        route_id = self.request.query_params.get('route', None)
        status_code = self.request.query_params.get('status', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)

        if route_id:
            queryset = queryset.filter(route_id=route_id)
        if status_code:
            queryset = queryset.filter(status_code=status_code)
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        return queryset.order_by('-created_at')[:1000]  # Limit to last 1000 entries


class RateLimitViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing rate limits"""

    queryset = RateLimit.objects.select_related('route')
    serializer_class = RateLimitSerializer

    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = RateLimit.objects.select_related('route')
        route_id = self.request.query_params.get('route', None)
        identifier = self.request.query_params.get('identifier', None)

        if route_id:
            queryset = queryset.filter(route_id=route_id)
        if identifier:
            queryset = queryset.filter(identifier=identifier)

        return queryset


@api_view(['GET'])
@permission_classes([AllowAny])
def gateway_stats(request):
    """Get gateway statistics"""
    # Calculate statistics
    total_services = Service.objects.count()
    active_services = Service.objects.filter(is_active=True).count()
    total_routes = Route.objects.count()
    active_routes = Route.objects.filter(is_active=True).count()

    # Request statistics (last 24 hours)
    yesterday = timezone.now() - timezone.timedelta(days=1)
    recent_logs = RequestLog.objects.filter(created_at__gte=yesterday)

    total_requests = recent_logs.count()
    avg_response_time = recent_logs.aggregate(
        avg_time=models.Avg('response_time')
    )['avg_time'] or 0

    error_requests = recent_logs.filter(status_code__gte=400).count()
    error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0

    # Top routes by request count
    top_routes = recent_logs.values('route__path', 'route__method').annotate(
        count=models.Count('id')
    ).order_by('-count')[:5]

    top_routes_list = [
        {'path': route['route__path'], 'method': route['route__method'], 'count': route['count']}
        for route in top_routes
    ]

    serializer = GatewayStatsSerializer({
        'total_services': total_services,
        'active_services': active_services,
        'total_routes': total_routes,
        'active_routes': active_routes,
        'total_requests': total_requests,
        'avg_response_time': round(avg_response_time, 2),
        'error_rate': round(error_rate, 2),
        'top_routes': top_routes_list
    })

    return Response(serializer.data)


class GatewayProxyView(APIView):
    """Main API Gateway proxy view"""

    permission_classes = [AllowAny]

    def dispatch(self, request, path=None, *args, **kwargs):
        """Override dispatch to handle all HTTP methods"""
        return self._handle_request(request, path)

    def _handle_request(self, request, path):
        """Handle incoming requests and proxy to appropriate service"""
        start_time = time.time()

        try:
            # Find matching route
            route = self._find_route(request.path, request.method)
            if not route:
                return HttpResponse(
                    json.dumps({'error': 'Route not found'}),
                    status=status.HTTP_404_NOT_FOUND,
                    content_type='application/json'
                )

            # Check if route is active
            if not route.is_active:
                return HttpResponse(
                    json.dumps({'error': 'Route is disabled'}),
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                    content_type='application/json'
                )

            # Check authentication if required
            if route.requires_auth:
                auth_result = self._check_authentication(request)
                if not auth_result['valid']:
                    return HttpResponse(
                        json.dumps({'error': auth_result['error']}),
                        status=status.HTTP_401_UNAUTHORIZED,
                        content_type='application/json'
                    )

            # Check rate limiting
            rate_limit_result = self._check_rate_limit(request, route)
            if not rate_limit_result['allowed']:
                return HttpResponse(
                    json.dumps({'error': 'Rate limit exceeded'}),
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                    content_type='application/json'
                )

            # Proxy the request
            response = self._proxy_request(request, route)

            # Log the request
            self._log_request(request, route, response, start_time)

            return response

        except Exception as e:
            logger.error(f"Gateway error: {str(e)}")
            # Log failed request
            self._log_request(request, None, None, start_time, error=str(e))
            return HttpResponse(
                json.dumps({'error': 'Internal gateway error'}),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content_type='application/json'
            )

    def _find_route(self, request_path, method):
        """Find matching route for the request"""
        routes = Route.objects.select_related('service')

        for route in routes:
            if route.matches_request(request_path, method):
                return route

        return None

    def _check_authentication(self, request):
        """Check authentication for the request"""
        # Check for API key in header
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return {'valid': False, 'error': 'API key required'}

        try:
            key_obj = APIKey.objects.get(key=api_key, is_active=True)
            if key_obj.is_expired():
                return {'valid': False, 'error': 'API key expired'}

            # Update last used timestamp
            key_obj.last_used = timezone.now()
            key_obj.save(update_fields=['last_used'])

            return {'valid': True, 'api_key': key_obj}
        except APIKey.DoesNotExist:
            return {'valid': False, 'error': 'Invalid API key'}

    def _check_rate_limit(self, request, route):
        """Check rate limiting for the request"""
        # Use IP address as identifier (could be enhanced with API key)
        identifier = self._get_client_ip(request)

        # Get current window
        now = timezone.now()
        window_start = now.replace(minute=0, second=0, microsecond=0)

        # Get or create rate limit record
        rate_limit, created = RateLimit.objects.get_or_create(
            identifier=identifier,
            route=route,
            window_start=window_start,
            defaults={'window_end': window_start + timezone.timedelta(hours=1)}
        )

        # Reset counter if window has changed
        if now >= rate_limit.window_end:
            rate_limit.request_count = 0
            rate_limit.window_start = window_start
            rate_limit.window_end = window_start + timezone.timedelta(hours=1)
            rate_limit.save()

        # Check if limit exceeded
        if rate_limit.is_limit_exceeded():
            return {'allowed': False}

        # Increment counter
        rate_limit.increment()
        return {'allowed': True}

    def _proxy_request(self, request, route):
        """Proxy request to the target service"""
        service = route.service
        service_url = service.get_full_url()

        # Build target URL
        target_url = f"{service_url}{request.path}"

        # Add query parameters
        if request.GET:
            target_url += f"?{request.GET.urlencode()}"

        # Prepare headers (remove gateway-specific headers)
        headers = {}
        for key, value in request.headers.items():
            if not key.lower().startswith('x-gateway'):
                headers[key] = value

        # Forward the request
        try:
            response = requests.request(
                method=request.method,
                url=target_url,
                headers=headers,
                data=request.body if request.body else None,
                timeout=30  # 30 second timeout
            )

            # Create Django response
            if response.headers.get('content-type', '').startswith('application/json'):
                content = response.text  # Use text which contains the JSON string
            else:
                content = response.text

            django_response = HttpResponse(
                content,
                status=response.status_code
            )

            # Set content type
            content_type = response.headers.get('content-type', 'text/plain')
            django_response['Content-Type'] = content_type

            # Copy other response headers
            for key, value in response.headers.items():
                if key.lower() not in ['content-length', 'content-encoding', 'transfer-encoding']:
                    django_response[key] = value

            return django_response

        except requests.RequestException as e:
            logger.error(f"Service request failed: {str(e)}")
            return HttpResponse(
                json.dumps({'error': 'Service unavailable'}),
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                content_type='application/json'
            )

    def _log_request(self, request, route, response, start_time, error=None):
        """Log the request"""
        response_time = (time.time() - start_time) * 1000

        # Extract API key if present
        api_key = None
        api_key_header = request.headers.get('X-API-Key')
        if api_key_header:
            try:
                api_key = APIKey.objects.get(key=api_key_header)
            except APIKey.DoesNotExist:
                pass

        RequestLog.objects.create(
            route=route,
            method=request.method,
            path=request.path,
            status_code=response.status_code if response else 500,
            response_time=round(response_time, 2),
            user_agent=request.headers.get('User-Agent', ''),
            ip_address=self._get_client_ip(request),
            api_key=api_key
        )

    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.headers.get('X-Forwarded-For')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
