from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'services', views.ServiceViewSet)
router.register(r'routes', views.RouteViewSet)
router.register(r'api-keys', views.APIKeyViewSet)
router.register(r'request-logs', views.RequestLogViewSet)
router.register(r'rate-limits', views.RateLimitViewSet)

urlpatterns = [
    # API Gateway management endpoints
    path('api/', include(router.urls)),

    # Gateway statistics
    path('api/stats/', views.gateway_stats, name='gateway-stats'),

    # Proxy all other requests to backend services
    re_path(r'^(?P<path>.*)$', views.GatewayProxyView.as_view(), name='gateway-proxy'),
]