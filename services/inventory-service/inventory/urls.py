from django.urls import path
from .views import InventoryView, run_inventory_tests

urlpatterns = [
    path('inventory/', InventoryView.as_view(), name='inventory-list'),
    path('inventory/tests/', run_inventory_tests, name='inventory-tests'),
]