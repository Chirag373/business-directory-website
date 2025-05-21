from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.promotor_signup, name='promotor_signup'),
    path('dashboard/', views.promotor_dashboard, name='promotor_dashboard'),
]