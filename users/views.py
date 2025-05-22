from django.shortcuts import render

# Create your views here.
def signup(request):
    return render(request, 'users/signup.html')

def requestor_signup(request):
    return render(request, 'users/requestor_signup.html')

def consumer_dashboard(request):
    return render(request, 'users/consumer_dashboard.html')