from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('signup/requestor/', views.requestor_signup, name='requestor_signup'),
    path('dashboard/consumer/', views.consumer_dashboard, name='consumer_dashboard'),
]