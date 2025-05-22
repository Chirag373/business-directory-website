from django.shortcuts import render

# Create your views here.
def promotor_signup(request):
    return render(request, 'promotor/promotor_signup.html')

def promotor_dashboard(request):
    return render(request, 'promotor/promotor_dashboard.html')