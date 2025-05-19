from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('signup/', views.signup, name='signup'),
    path('signup/requestor/', views.requestor_signup, name='requestor_signup'),
    path('signup/handyman/', views.handyman_signup, name='handyman_signup'),
    path('signup/promotor/', views.promotor_signup, name='promotor_signup'),
    path('dashboard/consumer/', views.consumer_dashboard, name='consumer_dashboard'),
]