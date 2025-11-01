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
from stela.models.finanzas import Periodo, Balance, BalanceDetalle
from stela.models.catalogo import Catalogo, GrupoCuenta, Cuenta
from stela.services.analisis import analisis_vertical, analisis_horizontal
from stela.services.ratios import calcular_y_guardar_ratios
from stela.services.benchmark import benchmarking_por_ciiu, etiqueta_semaforo
from stela.services.estados import recalcular_saldos_detalle
from stela.services.plantillas import (
    generar_plantilla_catalogo_csv,
    generar_plantilla_catalogo_excel,
    generar_plantilla_estados_csv,
    generar_plantilla_estados_excel
)
from stela.models.ciiu import Ciiu
from stela.forms import CiiuForm, CatalogoUploadForm, CatalogoManualForm, MapeoCuentaForm
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect
from decimal import Decimal
import csv
import io
from openpyxl import load_workbook

from .forms.EmpresaForm import EmpresaForm,EmpresaEditForm

from django.db import transaction
from stela.services.ratios import calcular_ratios

from django.http import JsonResponse
from stela.models.finanzas import RatioDef, ResultadoRatio
from django.db.models import Prefetch

# Create your views here.
def landing(request):
    return render(request, "stela/landing.html")


@login_required
def dashboard(request):
    """Vista del dashboard con información de empresas y catálogos"""
    user = request.user
    empresas = Empresa.objects.filter(usuario=user).order_by('razon_social')
    
    # Búsqueda por empresa
    query = request.GET.get('q', '').strip()
    if query:
        empresas = empresas.filter(razon_social__icontains=query)
    
    # Obtener información de catálogos y estados financieros por empresa
    empresas_data = []
    for empresa in empresas:
        catalogo = Catalogo.objects.filter(empresa=empresa).first()
        periodos = Periodo.objects.filter(empresa=empresa).order_by('-anio', '-mes')
        balances = Balance.objects.filter(empresa=empresa).select_related('periodo').order_by('-periodo__anio', '-periodo__mes')
        
        empresas_data.append({
            'empresa': empresa,
            'catalogo': catalogo,
            'tiene_catalogo': catalogo is not None,
            'num_periodos': periodos.count(),
            'num_balances': balances.count(),
            'periodos': periodos[:5],  # Últimos 5 períodos
        })
    
    context = {
        'empresas_data': empresas_data,
        'tiene_empresas': empresas.exists(),
        'query': query,
    }
    return render(request, "dashboard/dashboard.html", context)


@login_required
def empresa_detalles(request, empresa_nit):
    """Vista de detalles de una empresa: estados financieros y catálogo"""
    user = request.user
    empresa = get_object_or_404(Empresa, nit=empresa_nit, usuario=user)
    
    # Obtener catálogo de la empresa
    catalogo = Catalogo.objects.filter(empresa=empresa).first()
    cuentas = []
    if catalogo:
        cuentas = Cuenta.objects.filter(grupo__catalogo=catalogo).select_related('grupo').order_by('codigo')
    
    # Obtener períodos y balances
    periodos = Periodo.objects.filter(empresa=empresa).order_by('-anio', '-mes')
    
    # Agrupar balances por período
    balances_por_periodo = {}
    for periodo in periodos:
        balances = Balance.objects.filter(empresa=empresa, periodo=periodo).select_related('periodo')
        balances_por_periodo[periodo] = {
            'balance': balances.filter(tipo_balance='BAL').first(),
            'resultados': balances.filter(tipo_balance='RES').first(),
        }
    
    context = {
        'empresa': empresa,
        'catalogo': catalogo,
        'cuentas': cuentas,
        'tiene_catalogo': catalogo is not None,
        'periodos': periodos,
        'balances_por_periodo': balances_por_periodo,
    }
    return render(request, "dashboard/empresa_detalles.html", context)


def crearEmpresa(request):
    # Initialize form variable outside the if block
    form = EmpresaForm()

    if request.method == 'POST':
        form = EmpresaForm(request.POST)

        if form.is_valid():
            empresa = form.save(commit=False)
            empresa.usuario = request.user
            empresa.save()
            return redirect('dashboard')

    context = {
        'form': form
    }
    return render(request, "stela/crear-empresa.html", context)


def editarEmpresa(request, nit):

    empresa = get_object_or_404(Empresa, nit=nit,
                                usuario=request.user)
    if request.method == 'POST':

        form = EmpresaEditForm(request.POST, instance=empresa)

        if form.is_valid():
            form.save()
            return redirect('dashboard')

    else:
        form = EmpresaEditForm(instance=empresa)

    context = {
        'form': form,
        'empresa': empresa
    }
    return render(request, "stela/editar-empresa.html", context)








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

#sexo de proyecciones
def projections(request):
    user = request.user
    empresas = Empresa.objects.filter(usuario=user)
    empresa_seleccionada = None
    ventas = []
    proyecciones_minimos = []
    proyecciones_porcentuales = []
    proyecciones_incremento_absoluto = []

    if request.method == "POST" and "archivo_excel" in request.FILES:
        empresa_nit = request.POST.get("empresa")
        empresa_seleccionada = Empresa.objects.get(nit=empresa_nit)
        archivo = request.FILES["archivo_excel"]

        # eliminar registros anteriores
        Venta.objects.filter(empresa=empresa_seleccionada).delete()

        # leer el excel
        try:
            df = pd.read_excel(archivo)
        except Exception as e:
            messages.error(request, f"Error al leer el archivo Excel: {e}")
            return redirect(f"{reverse('projections')}?empresa={empresa_nit}")

        # normalizar nombres de columnas
        df.columns = df.columns.str.strip().str.lower()

        # buscar las columnas de mes y valor
        col_mes = next((c for c in df.columns if "mes" in str(c).lower() or "fecha" in str(c).lower()), None)
        col_valor = next((c for c in df.columns if "valor" in str(c).lower() or "monto" in str(c).lower() or "venta" in str(c).lower()), None)

        # valida enr que existan las columnas
        if not col_mes or not col_valor:
            messages.error(
                request,
                "El archivo debe tener columnas llamadas 'Mes' y 'Valor'.",
            )
            return redirect(f"{reverse('projections')}?empresa={empresa_nit}")

        # si todo esta verygod validamos y guardamos
        try:
            for i, row in df.iterrows():
                # mes
                try:
                    fecha = pd.to_datetime(row[col_mes], errors="raise")
                except Exception:
                    messages.error(
                        request,
                        f"Error en la fila {i + 2}: la columna 'Mes' tiene un valor no válido ('{row[col_mes]}'). "
                        "Debe ser una fecha como 2024-01-01.",
                    )
                    return redirect(f"{reverse('projections')}?empresa={empresa_nit}")

                # valor
                try:
                    valor = float(row[col_valor])
                except Exception:
                    messages.error(
                        request,
                        f"Error en la fila {i + 2}: la columna 'Valor' tiene un valor no numérico ('{row[col_valor]}').",
                    )
                    return redirect(f"{reverse('projections')}?empresa={empresa_nit}")

                # guarda en ventas
                Venta.objects.create(
                    empresa=empresa_seleccionada,
                    mes_venta=fecha,
                    saldo_venta=valor,
                    anio=fecha.year,
                    proyeccion=False
                )

            # verygud
            messages.success(
                request,
                f"Ventas guardadas correctamente para la empresa {empresa_seleccionada.razon_social}.",
            )

        except Exception as e:
            messages.error(request, f"Error inesperado al procesar el archivo: {e}")
            return redirect(f"{reverse('projections')}?empresa={empresa_nit}")

            # Redirigir para recargar datos y mostrar mensaje
            return redirect(f"{reverse('projections')}?empresa={empresa_nit}")
        
    # procesar la empresa seleccionada
    empresa_nit = request.GET.get("empresa")
    if empresa_nit:
        empresa_seleccionada = Empresa.objects.get(nit=empresa_nit)

        # ventas reales
        ventas = Venta.objects.filter(
            empresa=empresa_seleccionada, proyeccion=False
        ).order_by("mes_venta")

        # minimos cuadrados
        y = np.array([v.saldo_venta for v in ventas])
        n = len(y)
        if n > 1:
            x = np.arange(1, n + 1)
            sum_x = np.sum(x)
            sum_y = np.sum(y)
            sum_xy = np.sum(x * y)
            sum_x2 = np.sum(x**2)

            b = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)
            a = (sum_y - b * sum_x) / n

            x_future = np.arange(n + 1, n + 13)
            y_future = a + b * x_future
            anio_base = ventas.last().anio

            proyecciones_minimos = [
                {
                    "mes_proyectado": datetime(anio_base + 1, i + 1, 1),
                    "valor_proyectado": y_val,
                }
                for i, y_val in enumerate(y_future)
            ]

        # incremento porcentual
        valores = [v.saldo_venta for v in ventas]
        if len(valores) > 1:
            incrementos = [
                (valores[i] - valores[i - 1]) / valores[i - 1]
                for i in range(1, len(valores))
            ]
            prom_incremento = np.mean(incrementos)
            ultimo_valor = valores[-1]
            anio_base = ventas.last().anio

            for mes in range(1, 13):
                nuevo_valor = ultimo_valor * (1 + prom_incremento)
                ultimo_valor = nuevo_valor
                proyecciones_porcentuales.append(
                    {
                        "mes_proyectado": datetime(anio_base + 1, mes, 1),
                        "valor_proyectado": nuevo_valor,
                    }
                )

        # incremento absoluto
        if len(valores) > 1:
            incrementos_abs = [
                (valores[i] - valores[i - 1]) for i in range(1, len(valores))
            ]
            prom_incremento_abs = np.mean(incrementos_abs)
            ultimo_valor = valores[-1]
            anio_base = ventas.last().anio

            for mes in range(1, 13):
                nuevo_valor = ultimo_valor + prom_incremento_abs
                ultimo_valor = nuevo_valor
                proyecciones_incremento_absoluto.append(
                    {
                        "mes_proyectado": datetime(anio_base + 1, mes, 1),
                        "valor_proyectado": nuevo_valor,
                    }
                )
                
    contexto = {
        "empresas": empresas,
        "empresa_seleccionada": empresa_seleccionada,
        "ventas": ventas,
        "proyecciones": proyecciones_minimos,
        "proyecciones_porcentuales": proyecciones_porcentuales,
        "proyecciones_incremento_absoluto": proyecciones_incremento_absoluto,
    }
    return render(request, "projections/projection.html", contexto)

#filtro para las proyecciones
def money(value):
    try:
        return "${:,.2f}".format(float(value))
    except (ValueError, TypeError):
        return "$0.00"


# ========== VISTAS CRUD PARA CIIU (CATÁLOGOS) ==========

@access_required('011')
def ciiu_list(request):
    """
    Lista todos los códigos CIIU con paginación y búsqueda.
    """
    query = request.GET.get('q', '').strip()
    ciiu_list = Ciiu.objects.all().order_by('codigo')
    
    # Búsqueda por código o descripción
    if query:
        ciiu_list = ciiu_list.filter(
            codigo__icontains=query
        ) | ciiu_list.filter(
            descripcion__icontains=query
        )
    
    # Paginación
    paginator = Paginator(ciiu_list, 25)  # 25 por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Contar empresas asociadas para cada CIIU
    for ciiu in page_obj:
        ciiu.empresas_count = Empresa.objects.filter(idCiiu=ciiu).count()
    
    context = {
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'stela/catalogo/list.html', context)


@access_required('011')
def ciiu_create(request):
    """
    Crea un nuevo código CIIU.
    """
    if request.method == 'POST':
        form = CiiuForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Código CIIU creado correctamente.')
            return redirect('ciiu_list')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        form = CiiuForm()
    
    context = {
        'form': form,
        'titulo': 'Crear Código CIIU'
    }
    return render(request, 'stela/catalogo/create.html', context)


@access_required('011')
def ciiu_update(request, codigo):
    """
    Edita un código CIIU existente.
    """
    ciiu = get_object_or_404(Ciiu, codigo=codigo)
    
    if request.method == 'POST':
        form = CiiuForm(request.POST, instance=ciiu)
        if form.is_valid():
            form.save()
            messages.success(request, 'Código CIIU actualizado correctamente.')
            return redirect('ciiu_list')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        form = CiiuForm(instance=ciiu)
    
    # Contar empresas asociadas
    empresas_count = Empresa.objects.filter(idCiiu=ciiu).count()
    hijos_count = ciiu.hijos.count()
    
    context = {
        'form': form,
        'ciiu': ciiu,
        'titulo': 'Editar Código CIIU',
        'empresas_count': empresas_count,
        'hijos_count': hijos_count
    }
    return render(request, 'stela/catalogo/update.html', context)


@access_required('011')
def ciiu_delete(request, codigo):
    """
    Elimina un código CIIU (con validación de empresas e hijos).
    """
    ciiu = get_object_or_404(Ciiu, codigo=codigo)
    
    # Validar si tiene empresas asociadas
    empresas_count = Empresa.objects.filter(idCiiu=ciiu).count()
    hijos_count = ciiu.hijos.count()
    
    if request.method == 'POST':
        # Verificar nuevamente antes de eliminar
        if Empresa.objects.filter(idCiiu=ciiu).exists():
            messages.error(
                request,
                f'No se puede eliminar el código CIIU porque tiene {empresas_count} empresa(s) asociada(s).'
            )
            return redirect('ciiu_list')
        
        if ciiu.hijos.exists():
            messages.error(
                request,
                f'No se puede eliminar el código CIIU porque tiene {hijos_count} código(s) hijo(s).'
            )
            return redirect('ciiu_list')
        
        ciiu.delete()
        messages.success(request, 'Código CIIU eliminado correctamente.')
        return redirect('ciiu_list')
    
    context = {
        'ciiu': ciiu,
        'empresas_count': empresas_count,
        'hijos_count': hijos_count
    }
    return render(request, 'stela/catalogo/delete.html', context)


# ========== VISTAS PARA CATÁLOGO DE CUENTAS ==========

@login_required
def catalogo_upload_csv(request):
    """
    Vista para cargar catálogo desde CSV.
    Maneja los pasos 1, 2 y 3 del asistente:
    - Paso 1: Selección de empresa
    - Paso 2: Carga solo el catálogo (cuentas)
    - Paso 3: Carga estados financieros (debe/haber)
    """
    paso = request.GET.get('paso', '1')  # Por defecto paso 1 (Selecciona Empresa)
    empresa_nit_param = request.GET.get('empresa', '')  # Empresa desde parámetro URL
    
    if request.method == 'POST':
        empresa_nit = request.POST.get('empresa')
        anio = request.POST.get('anio')  # Año para el período de estados financieros
        archivo = request.FILES.get('archivo')
        
        if not empresa_nit or not archivo:
            messages.error(request, 'Faltan datos requeridos')
            return redirect('catalogo_upload')
        
        try:
            empresa = get_object_or_404(Empresa, nit=empresa_nit, usuario=request.user)
            
            # Crear o obtener catálogo (único por empresa, sin año)
            catalogo, created = Catalogo.objects.get_or_create(
                empresa=empresa
            )
            
            # Solo crear período si estamos en paso 3 (estados financieros) y hay año
            periodo = None
            if paso == '3' and anio:
                anio = int(anio)
                periodo, _ = Periodo.objects.get_or_create(
                    empresa=empresa,
                    anio=anio,
                    mes=None
                )
            
            # Detectar tipo de archivo y leer
            nombre_archivo = archivo.name.lower()
            es_excel = nombre_archivo.endswith(('.xlsx', '.xls'))
            
            creados = 0
            errores = []
            
            # Diccionario para agrupar por tipo de estado
            balances_por_tipo = {}
            
            if es_excel:
                # Procesar Excel
                wb = load_workbook(archivo, data_only=True)
                filas = []
                
                if paso == '2':
                    # Paso 2: Catálogo (una sola hoja "Catálogo")
                    hoja_nombre = 'Catálogo' if 'Catálogo' in wb.sheetnames else wb.active.title
                    ws = wb[hoja_nombre]
                    for row in ws.iter_rows(min_row=2, values_only=True):  # Empezar desde fila 2 (después de encabezados)
                        if row[0] and row[1]:  # Si hay código y nombre
                            filas.append({
                                'codigo': str(row[0]).strip() if row[0] else '',
                                'nombre': str(row[1]).strip() if row[1] else '',
                                'grupo': str(row[2]).strip() if len(row) > 2 and row[2] else '',
                                'naturaleza': str(row[3]).strip() if len(row) > 3 and row[3] else '',
                                'bg_bloque': str(row[4]).strip() if len(row) > 4 and row[4] else '',
                                'er_bloque': str(row[5]).strip() if len(row) > 5 and row[5] else '',
                                'ratio_tag': str(row[6]).strip() if len(row) > 6 and row[6] else '',
                                'tipo_estado': '',  # No aplica en paso 2
                                'debe': '0',
                                'haber': '0'
                            })
                else:
                    # Paso 3: Estados financieros (dos hojas)
                    # Leer hoja BalanceGeneral
                    if 'BalanceGeneral' in wb.sheetnames:
                        ws_balance = wb['BalanceGeneral']
                        for row in ws_balance.iter_rows(min_row=3, values_only=True):  # Empezar desde fila 3 (después de encabezados)
                            # Saltar filas vacías o que sean títulos de bloque
                            if not row[0] or not row[1]:
                                continue
                            # Saltar si es un subtotal (no tiene código numérico)
                            try:
                                codigo = str(row[0]).strip()
                                # Si el código no parece un código de cuenta, saltar
                                if not codigo or codigo.startswith('Total') or not codigo[0].isdigit():
                                    continue
                            except:
                                continue
                            
                            filas.append({
                                'codigo': codigo,
                                'nombre': str(row[1]).strip() if row[1] else '',
                                'grupo': '',  # Se obtendrá del catálogo
                                'naturaleza': '',  # Se obtendrá del catálogo
                                'tipo_estado': 'BAL',
                                'debe': str(row[2]) if row[2] is not None else '0',
                                'haber': str(row[3]) if row[3] is not None else '0'
                            })
                    
                    # Leer hoja EstadoResultados
                    if 'EstadoResultados' in wb.sheetnames:
                        ws_resultados = wb['EstadoResultados']
                        for row in ws_resultados.iter_rows(min_row=3, values_only=True):  # Empezar desde fila 3
                            # Saltar filas vacías o que sean subtotales
                            if not row[0] or not row[1]:
                                continue
                            # Saltar si es un subtotal (no tiene código numérico)
                            try:
                                codigo = str(row[0]).strip()
                                # Si el código no parece un código de cuenta, saltar
                                if not codigo or not codigo[0].isdigit():
                                    continue
                            except:
                                continue
                            
                            # Ahora la estructura es: Código, Cuenta, Debe, Haber, Total
                            filas.append({
                                'codigo': codigo,
                                'nombre': str(row[1]).strip() if row[1] else '',
                                'grupo': '',  # Se obtendrá del catálogo
                                'naturaleza': '',  # Se obtendrá del catálogo
                                'tipo_estado': 'RES',
                                'debe': str(row[2]) if row[2] is not None else '0',  # Columna 3 (índice 2)
                                'haber': str(row[3]) if row[3] is not None else '0'  # Columna 4 (índice 3)
                            })
                
                reader = filas
            else:
                # DEPRECATED: CSV está deprecado, solo Excel es soportado
                messages.error(request, 'El formato CSV está deprecado. Por favor usa el formato Excel (.xlsx o .xls)')
                return redirect('catalogo_upload')
            
            for i, row in enumerate(reader, start=2):
                try:
                    codigo = row.get('codigo', '').strip()
                    nombre = row.get('nombre', '').strip()
                    grupo_nombre = row.get('grupo', '').strip()
                    naturaleza = row.get('naturaleza', '').strip()
                    bg_bloque = row.get('bg_bloque', '').strip()
                    er_bloque = row.get('er_bloque', '').strip()
                    ratio_tag = row.get('ratio_tag', '').strip()
                    tipo_estado = row.get('tipo_estado', 'BAL').strip().upper()
                    
                    # Convertir debe y haber de forma segura
                    try:
                        debe_str = str(row.get('debe', '0') or '0').strip()
                        debe = Decimal(debe_str) if debe_str else Decimal('0')
                    except (ValueError, TypeError, Exception):
                        debe = Decimal('0')
                    
                    try:
                        haber_str = str(row.get('haber', '0') or '0').strip()
                        haber = Decimal(haber_str) if haber_str else Decimal('0')
                    except (ValueError, TypeError, Exception):
                        haber = Decimal('0')
                    
                    if not codigo:
                        errores.append(f"Fila {i}: Falta código de cuenta")
                        continue
                    
                    # Buscar cuenta en el catálogo para obtener información faltante
                    cuenta_existente = None
                    if codigo:
                        cuenta_existente = Cuenta.objects.filter(
                            grupo__catalogo=catalogo,
                            codigo=codigo
                        ).select_related('grupo').first()
                    
                    # Si la cuenta existe, usar sus datos para completar información faltante
                    if cuenta_existente:
                        if not grupo_nombre:
                            grupo_nombre = cuenta_existente.grupo.nombre
                        if not naturaleza:
                            naturaleza = cuenta_existente.grupo.naturaleza
                        if not nombre:
                            nombre = cuenta_existente.nombre
                        if not bg_bloque and cuenta_existente.bg_bloque:
                            bg_bloque = cuenta_existente.bg_bloque
                        if not er_bloque and cuenta_existente.er_bloque:
                            er_bloque = cuenta_existente.er_bloque
                        if not ratio_tag and cuenta_existente.ratio_tag:
                            ratio_tag = cuenta_existente.ratio_tag
                        cuenta = cuenta_existente
                    else:
                        # Si la cuenta no existe, solo continuar si es paso 3 (estados financieros)
                        # En paso 3, si no existe la cuenta, simplemente la ignoramos
                        if paso == '3':
                            # En estados financieros, si la cuenta no existe, la ignoramos
                            # El subtotal se mostrará en 0
                            continue
                        
                        # En paso 2 (catálogo), necesitamos crear la cuenta
                        # Validar que tengamos los datos mínimos
                        if not nombre or not grupo_nombre:
                            errores.append(f"Fila {i}: Faltan campos obligatorios (nombre o grupo) para crear cuenta {codigo}")
                            continue
                        
                        # Crear o obtener grupo
                        grupo, _ = GrupoCuenta.objects.get_or_create(
                            catalogo=catalogo,
                            nombre=grupo_nombre,
                            defaults={'naturaleza': naturaleza}
                        )
                        
                        # Actualizar naturaleza si no tenía
                        if not grupo.naturaleza and naturaleza:
                            grupo.naturaleza = naturaleza
                            grupo.save()
                        
                        # Crear cuenta
                        cuenta, created = Cuenta.objects.get_or_create(
                            grupo=grupo,
                            codigo=codigo,
                            defaults={
                                'nombre': nombre, 
                                'aparece_en_balance': True,
                                'bg_bloque': bg_bloque if bg_bloque else None,
                                'er_bloque': er_bloque if er_bloque else None,
                                'ratio_tag': ratio_tag if ratio_tag else None
                            }
                        )
                        
                        # Actualizar nombre, bloques y ratio_tag si cambiaron
                        actualizar = False
                        if cuenta.nombre != nombre:
                            cuenta.nombre = nombre
                            actualizar = True
                        if bg_bloque and cuenta.bg_bloque != bg_bloque:
                            cuenta.bg_bloque = bg_bloque
                            actualizar = True
                        if er_bloque and cuenta.er_bloque != er_bloque:
                            cuenta.er_bloque = er_bloque
                            actualizar = True
                        if ratio_tag and cuenta.ratio_tag != ratio_tag:
                            cuenta.ratio_tag = ratio_tag
                            actualizar = True
                        if actualizar:
                            cuenta.save()
                    
                    # En paso 2 solo se crean cuentas, no balances
                    # En paso 3 se crean balances con debe/haber
                    if paso == '3':
                        # Si hay debe/haber, crear balance y detalle
                        # Solo procesar si la cuenta existe (si no existe, se ignoró arriba)
                        # Procesar incluso si debe y haber son 0, para tener el registro completo
                        if cuenta:
                            # Crear o obtener balance según tipo
                            if tipo_estado not in balances_por_tipo:
                                balance, _ = Balance.objects.get_or_create(
                                    empresa=empresa,
                                    periodo=periodo,
                                    tipo_balance=tipo_estado
                                )
                                balances_por_tipo[tipo_estado] = balance
                            else:
                                balance = balances_por_tipo[tipo_estado]
                            
                            # Crear o actualizar detalle de balance
                            detalle, created = BalanceDetalle.objects.get_or_create(
                                balance=balance,
                                cuenta=cuenta,
                                defaults={'debe': debe, 'haber': haber}
                            )
                            if not created:
                                detalle.debe = debe
                                detalle.haber = haber
                                detalle.save()
                    
                    creados += 1
                    
                except Exception as e:
                    errores.append(f"Fila {i}: {str(e)}")
            
            # Recalcular saldos solo en paso 3 (cuando se crean balances)
            if paso == '3':
                for balance in balances_por_tipo.values():
                    recalcular_saldos_detalle(balance)
            
            if paso == '2':
                # Paso 2: Solo catálogo (sin debe/haber)
                if errores:
                    messages.warning(request, f"Se procesaron {creados} cuentas, pero hubo {len(errores)} errores.")
                else:
                    messages.success(request, f"Catálogo cargado correctamente. {creados} cuentas procesadas.")
                # Redirigir al paso 3 con el catálogo_id
                return redirect(f"{reverse('catalogo_upload')}?paso=3&empresa={empresa_nit}&catalogo_id={catalogo.id_catalogo}")
            else:
                # Paso 3: Estados financieros (con debe/haber)
                if errores:
                    messages.warning(request, f"Se procesaron {creados} filas, pero hubo {len(errores)} errores.")
                else:
                    messages.success(request, f"Estados financieros cargados correctamente. {creados} registros procesados.")
                # Redirigir al mapeo de cuentas
                return redirect(f"{reverse('catalogo_mapeo', args=[catalogo.id_catalogo])}")
                
        except Exception as e:
            messages.error(request, f"Error al procesar el archivo: {str(e)}")
    
    # Contexto para el template
    empresas = Empresa.objects.filter(usuario=request.user).order_by('razon_social')
    catalogo_id = request.GET.get('catalogo_id', '')
    
    # Si hay empresa en parámetro, verificar si ya tiene catálogo
    empresa_seleccionada = None
    if empresa_nit_param:
        try:
            empresa_seleccionada = Empresa.objects.get(nit=empresa_nit_param, usuario=request.user)
            catalogo_existente = Catalogo.objects.filter(empresa=empresa_seleccionada).first()
            if catalogo_existente:
                # Si ya tiene catálogo y estamos en paso 1, saltar al paso 3
                # Si estamos en paso 2, permitir actualizar el catálogo
                if paso == '1':
                    paso = '3'
                    catalogo_id = str(catalogo_existente.id_catalogo)
                    messages.info(request, f'Esta empresa ya tiene un catálogo cargado. Puedes cargar estados financieros para nuevos períodos.')
        except Empresa.DoesNotExist:
            pass
    
    # Si hay catálogo_id, obtener el catálogo para el paso 3
    catalogo = None
    if catalogo_id:
        try:
            catalogo = Catalogo.objects.get(pk=catalogo_id, empresa__usuario=request.user)
        except Catalogo.DoesNotExist:
            pass
    
    context = {
        'empresas_usuario': empresas,
        'paso': paso,
        'empresa_nit': empresa_nit_param or request.GET.get('empresa', ''),
        'catalogo_id': catalogo_id,
        'catalogo': catalogo,
        'tiene_catalogo': catalogo is not None
    }
    return render(request, 'stela/catalogo/upload.html', context)


@login_required
def catalogo_create_manual(request):
    """
    Vista para crear catálogo manualmente.
    """
    if request.method == 'POST':
        form = CatalogoManualForm(request.POST, user=request.user)
        if form.is_valid():
            empresa = form.cleaned_data['empresa']
            
            # Crear catálogo (único por empresa, sin año)
            catalogo, created = Catalogo.objects.get_or_create(
                empresa=empresa
            )
            
            if created:
                messages.success(request, f'Catálogo creado para {empresa.razon_social}')
            else:
                messages.info(request, f'El catálogo para {empresa.razon_social} ya existe')
            
            return redirect('dashboard')
    else:
        form = CatalogoManualForm(user=request.user)
    
    context = {
        'form': form,
        'titulo': 'Crear Catálogo Manualmente'
    }
    return render(request, 'stela/catalogo/create_manual.html', context)


@login_required
def catalogo_mapeo_cuentas(request, catalogo_id):
    """
    Vista para mapear cuentas a líneas de estado (para ratios).
    Pestaña oculta, no aparece en el menú principal.
    """
    catalogo = get_object_or_404(Catalogo, pk=catalogo_id, empresa__usuario=request.user)
    
    if request.method == 'POST':
        form = MapeoCuentaForm(request.POST, catalogo=catalogo)
        if form.is_valid():
            from stela.models.finanzas import LineaEstado, MapeoCuentaLinea
            
            # Procesar cada campo del formulario
            for field_name, cuenta in form.cleaned_data.items():
                if field_name.startswith('linea_') and cuenta:
                    clave_linea = field_name.replace('linea_', '')
                    try:
                        linea = LineaEstado.objects.get(clave=clave_linea)
                        
                        # Eliminar mapeos existentes para esta línea y cuenta
                        MapeoCuentaLinea.objects.filter(
                            linea=linea,
                            cuenta__grupo__catalogo=catalogo
                        ).delete()
                        
                        # Crear nuevo mapeo
                        MapeoCuentaLinea.objects.create(
                            cuenta=cuenta,
                            linea=linea,
                            signo=1
                        )
                    except LineaEstado.DoesNotExist:
                        pass
            
            messages.success(request, 'Mapeo de cuentas guardado correctamente.')
            return redirect('dashboard')
    else:
        form = MapeoCuentaForm(catalogo=catalogo)
    
    context = {
        'form': form,
        'catalogo': catalogo,
        'titulo': 'Mapeo de Cuentas para Ratios'
    }
    return render(request, 'stela/catalogo/mapeo_cuentas.html', context)


# ========== VISTAS PARA DESCARGAR PLANTILLAS ==========

@login_required
def descargar_plantilla_catalogo_csv(request):
    """
    DEPRECATED: Esta función está deprecada. Usa descargar_plantilla_catalogo_excel en su lugar.
    Descarga plantilla CSV de catálogo (solo para compatibilidad hacia atrás).
    """
    # Deprecado: redirigir a Excel o mostrar mensaje
    messages.warning(request, 'El formato CSV está deprecado. Por favor usa el formato Excel.')
    return redirect('descargar_plantilla_catalogo_excel')


@login_required
def descargar_plantilla_catalogo_excel(request):
    """Descarga plantilla Excel de catálogo"""
    output = generar_plantilla_catalogo_excel()
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="plantilla_catalogo.xlsx"'
    return response


@login_required
def descargar_plantilla_estados_csv(request):
    """
    DEPRECATED: Esta función está deprecada. Usa descargar_plantilla_estados_excel en su lugar.
    Descarga plantilla CSV de estados financieros (solo para compatibilidad hacia atrás).
    """
    catalogo_id = request.GET.get('catalogo_id', '')
    if catalogo_id:
        # Deprecado: redirigir a Excel
        messages.warning(request, 'El formato CSV está deprecado. Por favor usa el formato Excel.')
        return redirect('descargar_plantilla_estados_excel', catalogo_id=catalogo_id)
    else:
        messages.warning(request, 'El formato CSV está deprecado. Por favor usa el formato Excel.')
        return redirect('dashboard')


@login_required
def descargar_plantilla_estados_excel(request, catalogo_id):
    """Descarga plantilla Excel de estados financieros basada en catálogo"""
    catalogo = get_object_or_404(Catalogo, pk=catalogo_id, empresa__usuario=request.user)
    output = generar_plantilla_estados_excel(catalogo)
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="plantilla_estados_{catalogo.empresa.nit}.xlsx"'
    return response

def inf_vertical(request):
    empresa_nit = request.GET.get("empresa")
    periodo_id  = request.GET.get("periodo")
    estado      = request.GET.get("estado", "BAL")  # BAL | RES

    empresa = get_object_or_404(Empresa, nit=empresa_nit)
    periodo = get_object_or_404(Periodo, pk=periodo_id, empresa=empresa)

    data = analisis_vertical(empresa, periodo, estado)
    ctx = {"empresa": empresa, "periodo": periodo, "estado": estado, "filas": data}
    return render(request, "informes/vertical.html", ctx)

# ---- INFORME: Análisis Horizontal ----
def inf_horizontal(request):
    empresa_nit = request.GET.get("empresa")
    base_id     = request.GET.get("base")
    actual_id   = request.GET.get("actual")
    estado      = request.GET.get("estado", "BAL")

    empresa = get_object_or_404(Empresa, nit=empresa_nit)
    periodo_base  = get_object_or_404(Periodo, pk=base_id, empresa=empresa)
    periodo_act   = get_object_or_404(Periodo, pk=actual_id, empresa=empresa)

    filas = analisis_horizontal(empresa, periodo_base, periodo_act, estado)
    ctx = {"empresa": empresa, "estado": estado, "base": periodo_base, "actual": periodo_act, "filas": filas}
    return render(request, "informes/horizontal.html", ctx)

# ---- INFORME: Ratios ----
@transaction.atomic
def inf_ratios(request):
    empresa_nit = request.GET.get("empresa")
    periodo_id  = request.GET.get("periodo")

    empresa = get_object_or_404(Empresa, nit=empresa_nit)
    periodo = get_object_or_404(Periodo, pk=periodo_id, empresa=empresa)

    # Asegura que los ratios estén calculados para este periodo
    resultados = calcular_ratios(empresa, periodo)  # devuelve lista [{clave,nombre,valor}, ...]

    ctx = {"empresa": empresa, "periodo": periodo, "resultados": resultados}
    return render(request, "informes/ratios.html", ctx)

# ---- INFORME: Benchmark por CIIU (promedios del sector) ----
def inf_benchmark(request):
    empresa_nit = request.GET.get("empresa")
    periodo_id  = request.GET.get("periodo")

    empresa = get_object_or_404(Empresa, nit=empresa_nit)
    periodo = get_object_or_404(Periodo, pk=periodo_id)
    if not empresa.ciiu:
        messages.warning(request, "La empresa no tiene CIIU asociado.")
        return redirect("dashboard")

    bench = benchmarking_por_ciiu(empresa.ciiu, periodo)   # {clave: {nombre,promedio,desv}}
    propios = {r["clave"]: r for r in calcular_ratios(empresa, periodo)}
    # Unimos y aplicamos semáforo
    filas = []
    for clave, meta in bench.items():
        propio = propios.get(clave, {"valor": None})
        etiqueta = etiqueta_semaforo(propio["valor"], meta["promedio"], meta["desv"])
        filas.append({
            "clave": clave,
            "nombre": meta["nombre"],
            "valor": propio["valor"],
            "promedio": meta["promedio"],
            "desv": meta["desv"],
            "semaforo": etiqueta,
        })

    ctx = {"empresa": empresa, "periodo": periodo, "filas": filas, "ciiu": empresa.ciiu}
    return render(request, "informes/benchmark.html", ctx)

def _ultimos_periodos(empresa, n=3):
    # Devuelve los últimos n periodos (por año) para la empresa
    return list(
        Periodo.objects.filter(empresa=empresa)
        .order_by("-anio")[:n]
        .values_list("id_periodo", "anio")
    )[::-1]  # ascendentes por año

def ratios_series_json(request):
    """
    JSON con series de 5 ratios para los últimos 3 años de una empresa.
    GET: ?empresa=<NIT>&claves=LIQ_CORR,PRUEBA_ACIDA,ENDEUDAMIENTO,MARGEN_NETO,ROA&n=3
    """
    empresa_nit = request.GET.get("empresa")
    n = int(request.GET.get("n", 3))

    # ratios por defecto (ajusta a tus claves reales si difieren)
    default_claves = ["LIQ_CORR", "PRUEBA_ACIDA", "ENDEUDAMIENTO", "MARGEN_NETO", "ROA"]
    claves = request.GET.get("claves", ",".join(default_claves)).split(",")

    empresa = Empresa.objects.get(nit=empresa_nit)
    periodos = _ultimos_periodos(empresa, n=n)  # [(id, anio), ...]
    periodo_ids = [p[0] for p in periodos]
    anios = [p[1] for p in periodos]

    # Obtén definiciones de ratios disponibles
    defs = {r.clave: r.nombre for r in RatioDef.objects.filter(clave__in=claves)}

    # Trae resultados en bloque
    resultados = (
        ResultadoRatio.objects
        .filter(empresa=empresa, periodo_id__in=periodo_ids, ratio__clave__in=claves)
        .select_related("periodo", "ratio")
        .order_by("ratio__clave", "periodo__anio")
    )

    # Estructura: {clave: {"nombre":..., "valores":[None/num por anio en orden]}, ...}
    series = {c: {"nombre": defs.get(c, c), "valores": [None]*len(periodo_ids)} for c in claves}
    idx_por_anio = {anio: i for i, anio in enumerate(anios)}

    for r in resultados:
        clave = r.ratio.clave
        anio = r.periodo.anio
        i = idx_por_anio.get(anio)
        if i is not None:
            # r.valor puede ser Decimal o None
            series[clave]["valores"][i] = float(r.valor) if r.valor is not None else None

    data = {
        "empresa": {"nit": empresa.nit, "razon": empresa.razon_social},
        "anios": anios,
        "series": series,  # dict
    }
    return JsonResponse(data)

def ratios_graficas(request):
    """
    Página con 5 gráficas de ratios usando Chart.js.
    Espera ?empresa=<NIT> (opcionalmente &claves=...&n=3)
    """
    empresa_nit = request.GET.get("empresa")
    claves = request.GET.get("claves", "LIQ_CORR,PRUEBA_ACIDA,ENDEUDAMIENTO,MARGEN_NETO,ROA")
    n = request.GET.get("n", "3")

    ctx = {
        "empresa_nit": empresa_nit,
        "claves": claves,
        "n": n,
    }
    return render(request, "informes/ratios_graficas.html", ctx)