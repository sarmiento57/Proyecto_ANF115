from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.decorators import access_required


# Create your views here.
def landing(request):
    return render(request, "stela/landing.html")

@access_required('010')
def dashboard(request):
    return render(request, "dashboard/dashboard.html")