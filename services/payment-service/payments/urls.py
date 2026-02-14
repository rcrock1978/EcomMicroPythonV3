from django.urls import path
from .views import PaymentView, run_payment_tests

urlpatterns = [
    path('payments/', PaymentView.as_view(), name='payment-list'),
    path('payments/tests/', run_payment_tests, name='payment-tests'),
]