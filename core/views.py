from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'home.html')

def contact(request):
    return render(request, 'contact.html')

def signup(request):
    return render(request, 'signup.html')

def promotor_signup(request):
    return render(request, 'promotor_signup.html')