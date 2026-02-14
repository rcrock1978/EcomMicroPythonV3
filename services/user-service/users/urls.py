from django.urls import path
from .views import UserView, run_user_tests

urlpatterns = [
    path('users/', UserView.as_view(), name='user-list'),
    path('users/tests/', run_user_tests, name='user-tests'),
]