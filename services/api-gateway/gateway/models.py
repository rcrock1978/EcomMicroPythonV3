from django.db import models
from django.core.exceptions import ValidationError
import re


class Service(models.Model):
    """Model representing a backend service"""

    SERVICE_TYPES = [
        ('product', 'Product Service'),
        ('user', 'User Service'),
        ('order', 'Order Service'),
        ('payment', 'Payment Service'),
        ('inventory', 'Inventory Service'),
        ('frontend', 'Frontend Service'),
    ]

    name = models.CharField(max_length=100, unique=True, help_text="Service name")
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES, help_text="Type of service")
    base_url = models.URLField(help_text="Base URL of the service")
    port = models.PositiveIntegerField(default=8000, help_text="Service port")
    is_active = models.BooleanField(default=True, help_text="Whether the service is active")
    health_check_url = models.URLField(blank=True, null=True, help_text="Health check endpoint")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.service_type}) - {self.base_url}:{self.port}"

    def clean(self):
        """Validate service data"""
        if self.port < 1 or self.port > 65535:
            raise ValidationError("Port must be between 1 and 65535")

        # Validate URL format
        if not self.base_url.startswith(('http://', 'https://')):
            raise ValidationError("Base URL must start with http:// or https://")

    def get_full_url(self):
        """Get the full service URL"""
        return f"{self.base_url}:{self.port}"


class Route(models.Model):
    """Model representing API routes"""

    HTTP_METHODS = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
    ]

    path = models.CharField(max_length=255, help_text="API path pattern")
    method = models.CharField(max_length=10, choices=HTTP_METHODS, default='GET')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='routes')
    is_active = models.BooleanField(default=True)
    requires_auth = models.BooleanField(default=False, help_text="Whether route requires authentication")
    rate_limit = models.PositiveIntegerField(default=100, help_text="Requests per minute limit")
    description = models.TextField(blank=True, help_text="Route description")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['path', 'method']
        ordering = ['path', 'method']

    def __str__(self):
        return f"{self.method} {self.path} -> {self.service.name}"

    def clean(self):
        """Validate route data"""
        # Validate path format
        if not self.path.startswith('/'):
            raise ValidationError("Path must start with '/'")

        # Validate rate limit
        if self.rate_limit < 1:
            raise ValidationError("Rate limit must be at least 1")

    def matches_request(self, request_path, request_method):
        """Check if this route matches the given request"""
        if self.method != request_method:
            return False

        # Simple pattern matching (could be enhanced with regex)
        if self.path.endswith('*'):
            # Wildcard matching
            prefix = self.path[:-1]
            return request_path.startswith(prefix)
        else:
            return self.path == request_path


class APIKey(models.Model):
    """Model for API key authentication"""

    key = models.CharField(max_length=255, unique=True, help_text="API key")
    name = models.CharField(max_length=100, help_text="Key name/owner")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='api_keys')
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(blank=True, null=True, help_text="Expiration date")
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(blank=True, null=True, help_text="Last usage timestamp")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.key[:10]}..."

    def is_expired(self):
        """Check if the API key is expired"""
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False


class RequestLog(models.Model):
    """Model for logging API requests"""

    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, blank=True)
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=500)
    status_code = models.PositiveIntegerField()
    response_time = models.FloatField(help_text="Response time in milliseconds")
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField()
    api_key = models.ForeignKey(APIKey, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['status_code']),
            models.Index(fields=['route']),
        ]

    def __str__(self):
        return f"{self.method} {self.path} - {self.status_code} ({self.response_time}ms)"


class RateLimit(models.Model):
    """Model for rate limiting"""

    identifier = models.CharField(max_length=255, help_text="Rate limit identifier (IP, API key, etc.)")
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    request_count = models.PositiveIntegerField(default=0)
    window_start = models.DateTimeField()
    window_end = models.DateTimeField()

    class Meta:
        unique_together = ['identifier', 'route', 'window_start']

    def __str__(self):
        return f"{self.identifier} - {self.route.path} ({self.request_count} requests)"

    def is_limit_exceeded(self):
        """Check if rate limit is exceeded"""
        return self.request_count >= self.route.rate_limit

    def increment(self):
        """Increment request count"""
        self.request_count += 1
        self.save()
