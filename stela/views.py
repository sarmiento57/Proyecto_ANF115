from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.decorators import access_required
import pandas as pd
import numpy as np
from datetime import datetime
from django.shortcuts import redirect
from stela.models.empresa import Empresa
from stela.models.venta import Venta
from django.urls import reverse
from django.contrib import messages


# Create your views here.
def landing(request):
    return render(request, "stela/landing.html")


def dashboard(request):
    return render(request, "dashboard/dashboard.html")

def crearEmpresa(request):
    return render(request, "stela/base.html")

def tools(request):
    return render(request,'tools/tools.html')