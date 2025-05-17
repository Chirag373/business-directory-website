from django.shortcuts import render

# Create your views here.
def signup_handyman(request):
    return render(request, 'handyman_signup.html')