from django.http import HttpResponse
from django.shortcuts import render

def dashboard(request):
    return HttpResponse("Hello, world. You're at the polls page.")
