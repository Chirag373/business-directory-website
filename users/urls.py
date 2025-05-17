from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_consumer, name='signup_consumer'),
]