from django.urls import path
from .views import ProductView, ProductDetailView, run_product_tests

urlpatterns = [
    path('products/', ProductView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('products/tests/', run_product_tests, name='product-tests'),
]