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

from django.shortcuts import get_object_or_404
from django.contrib import messages
from stela.models.empresa import Empresa
from stela.models.finanzas import Periodo
from stela.services.analisis import analisis_vertical, analisis_horizontal
from stela.services.ratios import calcular_y_guardar_ratios
from stela.services.benchmark import benchmarking_por_ciiu, etiqueta_semaforo


# Create your views here.
def landing(request):
    return render(request, "stela/landing.html")


def dashboard(request):
    return render(request, "dashboard/dashboard.html")

def crearEmpresa(request):
    return render(request, "stela/base.html")

def tools(request):
    return render(request,'tools/tools.html')

def tools_finanzas(request):
    # parámetros: ?nit=...&per_base=ID&periodo&per_act=ID&periodo&estado=RES|BAL
    nit = request.GET.get('nit')
    estado = request.GET.get('estado', 'RES')
    per_base_id = request.GET.get('per_base')
    per_act_id  = request.GET.get('per_act')

    ctx = {'estado': estado}
    if not (nit and per_act_id):
        messages.info(request, "Selecciona empresa y período para calcular.")
        return render(request, "tools/tools.html", ctx)

    empresa = get_object_or_404(Empresa, pk=nit)
    p_act   = get_object_or_404(Periodo, pk=per_act_id)

    # Ratios + vertical del período actual
    ratios = calcular_y_guardar_ratios(empresa, p_act, tipo_estado=estado)
    vertical_act = analisis_vertical(empresa, p_act, estado)

    # Horizontal si hay base
    horizontal_rows = []
    vertical_base = []
    if per_base_id:
        p_base = get_object_or_404(Periodo, pk=per_base_id)
        horizontal_rows = analisis_horizontal(empresa, p_base, p_act, estado)
        vertical_base = analisis_vertical(empresa, p_base, estado)

    # Benchmark por CIIU
    ratios_bench = []
    if getattr(empresa, 'idCiiu_id', None):
        bench = benchmarking_por_ciiu(empresa.idCiiu, p_act)
        for r in ratios:
            b = bench.get(r['clave'])
            if b:
                sem = etiqueta_semaforo(r['valor'], b['promedio'], b['desv'])
                ratios_bench.append({**r, **b, 'semaforo': sem})
            else:
                ratios_bench.append({**r, 'promedio': None, 'desv': None, 'semaforo': 'NA'})

    ctx.update({
        'empresa': empresa,
        'per_act': p_act,
        'per_base_id': per_base_id,
        'vertical_act': vertical_act,
        'vertical_base': vertical_base,
        'horizontal_rows': horizontal_rows,
        'ratios_rows': ratios_bench or ratios,
    })
    return render(request, "tools/tools.html", ctx)