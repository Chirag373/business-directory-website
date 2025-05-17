from django.urls import path
from . import views


urlpatterns = [
        path('signup/', views.signup_handyman, name='signup_handyman'),

]