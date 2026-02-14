from rest_framework import serializers
from .models import Service, Route, APIKey, RequestLog, RateLimit


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer for Service model"""

    routes_count = serializers.SerializerMethodField()
    full_url = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            'id', 'name', 'service_type', 'base_url', 'port', 'is_active',
            'health_check_url', 'full_url', 'routes_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'routes_count', 'full_url']

    def get_routes_count(self, obj):
        """Get count of active routes for this service"""
        return obj.routes.filter(is_active=True).count()

    def get_full_url(self, obj):
        """Get the full service URL"""
        return obj.get_full_url()

    def validate_port(self, value):
        """Validate port number"""
        if value < 1 or value > 65535:
            raise serializers.ValidationError("Port must be between 1 and 65535")
        return value

    def validate_base_url(self, value):
        """Validate base URL"""
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("Base URL must start with http:// or https://")
        return value


class RouteSerializer(serializers.ModelSerializer):
    """Serializer for Route model"""

    service_name = serializers.CharField(source='service.name', read_only=True)
    service_type = serializers.CharField(source='service.service_type', read_only=True)

    class Meta:
        model = Route
        fields = [
            'id', 'path', 'method', 'service', 'service_name', 'service_type',
            'is_active', 'requires_auth', 'rate_limit', 'description',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'service_name', 'service_type']

    def validate_path(self, value):
        """Validate path format"""
        if not value.startswith('/'):
            raise serializers.ValidationError("Path must start with '/'")
        return value

    def validate_rate_limit(self, value):
        """Validate rate limit"""
        if value < 1:
            raise serializers.ValidationError("Rate limit must be at least 1")
        return value


class APIKeySerializer(serializers.ModelSerializer):
    """Serializer for APIKey model"""

    service_name = serializers.CharField(source='service.name', read_only=True)
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = APIKey
        fields = [
            'id', 'name', 'service', 'service_name', 'is_active',
            'expires_at', 'is_expired', 'last_used', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'is_expired']
        extra_kwargs = {
            'key': {'write_only': True}  # Hide key in responses for security
        }

    def get_is_expired(self, obj):
        """Check if API key is expired"""
        return obj.is_expired()

    def validate_expires_at(self, value):
        """Validate expiration date"""
        from django.utils import timezone
        if value and value <= timezone.now():
            raise serializers.ValidationError("Expiration date must be in the future")
        return value


class RequestLogSerializer(serializers.ModelSerializer):
    """Serializer for RequestLog model"""

    route_path = serializers.CharField(source='route.path', read_only=True)
    route_method = serializers.CharField(source='route.method', read_only=True)
    api_key_name = serializers.CharField(source='api_key.name', read_only=True)

    class Meta:
        model = RequestLog
        fields = [
            'id', 'route', 'route_path', 'route_method', 'method', 'path',
            'status_code', 'response_time', 'user_agent', 'ip_address',
            'api_key', 'api_key_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'route_path', 'route_method', 'api_key_name']


class RateLimitSerializer(serializers.ModelSerializer):
    """Serializer for RateLimit model"""

    route_path = serializers.CharField(source='route.path', read_only=True)
    is_limit_exceeded = serializers.SerializerMethodField()

    class Meta:
        model = RateLimit
        fields = [
            'id', 'identifier', 'route', 'route_path', 'request_count',
            'window_start', 'window_end', 'is_limit_exceeded'
        ]
        read_only_fields = ['id', 'is_limit_exceeded']

    def get_is_limit_exceeded(self, obj):
        """Check if rate limit is exceeded"""
        return obj.is_limit_exceeded()


class GatewayStatsSerializer(serializers.Serializer):
    """Serializer for gateway statistics"""

    total_services = serializers.IntegerField()
    active_services = serializers.IntegerField()
    total_routes = serializers.IntegerField()
    active_routes = serializers.IntegerField()
    total_requests = serializers.IntegerField()
    avg_response_time = serializers.FloatField()
    error_rate = serializers.FloatField()
    top_routes = serializers.ListField(child=serializers.DictField())


class HealthCheckSerializer(serializers.Serializer):
    """Serializer for health check responses"""

    service = serializers.CharField()
    status = serializers.CharField()
    response_time = serializers.FloatField()
    timestamp = serializers.DateTimeField()
    details = serializers.DictField(required=False)