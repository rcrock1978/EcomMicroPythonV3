from django.urls import path
from .views import OrderView, run_order_tests

urlpatterns = [
    path('orders/', OrderView.as_view(), name='order-list'),
    path('orders/tests/', run_order_tests, name='order-tests'),
]