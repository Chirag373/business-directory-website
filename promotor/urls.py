from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.promotor_signup, name='promotor_signup'),
]