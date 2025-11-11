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
from stela.models.finanzas import Periodo, Balance, BalanceDetalle, ResultadoRatio
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
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from decimal import Decimal
import csv
import io
from openpyxl import load_workbook

from .forms.EmpresaForm import EmpresaForm,EmpresaEditForm

from .models.empresa import Empresa
from .models.finanzas import RatioDef, Periodo, ResultadoRatio, BalanceDetalle
from .models.catalogo import Catalogo, Cuenta

# Create your views here.
def landing(request):
    return render(request, "stela/landing.html")


@access_required('002')
def dashboard(request):
    """Vista del dashboard con información de empresas y catálogos"""
    user = request.user

    # Mostrar mensaje solo una vez por sesión
    if not request.session.get('bienvenida_mostrada'):
        messages.success(request, f'Bienvenido, {user.first_name} {user.last_name}')
        request.session['bienvenida_mostrada'] = True
        
    # se cambio por el nuevo campo many to many 
    empresas = Empresa.objects.filter(usuario=user).distinct().order_by('razon_social')
    
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


@access_required('003')
def empresa_detalles(request, empresa_nit):
    """Vista de detalles de una empresa: estados financieros y catálogo"""
    user = request.user
    #se cambio por el nuevo campo many to many
    empresa = get_object_or_404(Empresa.objects.filter(usuario=user), nit=empresa_nit)
    
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

@access_required('041', stay_on_page=True)
def crearEmpresa(request):
    # Initialize form variable outside the if block
    form = EmpresaForm()

    if request.method == 'POST':
        form = EmpresaForm(request.POST)

        if form.is_valid():
            try:
                empresa = form.save(commit=False)
                empresa.save()  # Guardar primero para que tenga ID
                empresa.usuario.add(request.user)  # Luego agregar usuario (ManyToMany)
                messages.success(request, f'Empresa {empresa.razon_social} creada exitosamente.')
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f'Error al crear la empresa: {str(e)}')
                # Log del error para debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Error al crear empresa: {e}', exc_info=True)

    context = {
        'form': form
    }
    return render(request, "stela/crear-empresa.html", context)

@access_required('010', stay_on_page=True)
def eliminar_balance(request, balance_id):
    """
    Vista para eliminar un estado financiero (Balance) y todos sus detalles.
    También elimina los ratios calculados para ese período si ya no hay balances.
    """
    from stela.models.finanzas import Balance, BalanceDetalle, ResultadoRatio, Periodo
    
    balance = get_object_or_404(
        Balance.objects.select_related('empresa', 'periodo'),
        pk=balance_id,
        empresa__usuario=request.user
    )
    
    empresa = balance.empresa
    periodo = balance.periodo
    tipo_balance = balance.get_tipo_balance_display()
    
    if request.method == 'POST':
        try:
            # Eliminar el balance (esto eliminará automáticamente todos los BalanceDetalle por CASCADE)
            balance.delete()
            
            # Verificar si el período ya no tiene balances
            balances_restantes = Balance.objects.filter(periodo=periodo).count()
            
            # Si no quedan balances, eliminar también los ratios calculados para ese período
            if balances_restantes == 0:
                ResultadoRatio.objects.filter(empresa=empresa, periodo=periodo).delete()
                messages.info(request, f'Se eliminaron también los ratios calculados para el período {periodo}.')
            
            messages.success(request, f'{tipo_balance} del período {periodo} eliminado correctamente.')
            return redirect('empresa_detalles', empresa_nit=empresa.nit)
        except Exception as e:
            messages.error(request, f'Error al eliminar el estado financiero: {str(e)}')
            return redirect('empresa_detalles', empresa_nit=empresa.nit)
    
    # GET: Mostrar confirmación
    context = {
        'balance': balance,
        'empresa': empresa,
        'periodo': periodo,
        'tipo_balance': tipo_balance,
        'num_detalles': balance.detalles.count()
    }
    return render(request, 'stela/balance/confirmar_eliminar.html', context)

@access_required('042', stay_on_page=True)
def editarEmpresa(request, nit):
    empresa = get_object_or_404(Empresa.objects.filter(usuario=request.user), nit=nit)
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

@access_required('005')
def tools(request):
    return render(request,'tools/tools.html')

@access_required('040', stay_on_page=True)
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

    # se cambio por el nuevo campo many to many
    empresa = get_object_or_404(Empresa.objects.filter(usuario=request.user), pk=nit)
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

@access_required('006')
def projections(request):
    user = request.user
    #se cambio por el nuevo campo many to many
    empresas = Empresa.objects.filter(usuario=user).distinct()
    empresa_seleccionada = None
    ventas = []
    proyecciones_minimos = []
    proyecciones_porcentuales = []
    proyecciones_incremento_absoluto = []

    if request.method == "POST" and "archivo_excel" in request.FILES:
        empresa_nit = request.POST.get("empresa")
        # se cambio por el nuevo campo many to many
        empresa_seleccionada = get_object_or_404(Empresa.objects.filter(usuario=user), nit=empresa_nit)
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
        # se cambio por el nuevo campo many to many
        empresa_seleccionada = get_object_or_404(Empresa.objects.filter(usuario=user), nit=empresa_nit)

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

@access_required('007')
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
        ciiu.empresas_count = Empresa.objects.filter(ciiu=ciiu).count()
    
    context = {
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'stela/catalogo/list.html', context)


@access_required('036', stay_on_page=True)
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


@access_required('037', stay_on_page=True)
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
    empresas_count = Empresa.objects.filter(ciiu=ciiu).count()
    hijos_count = ciiu.hijos.count()
    
    context = {
        'form': form,
        'ciiu': ciiu,
        'titulo': 'Editar Código CIIU',
        'empresas_count': empresas_count,
        'hijos_count': hijos_count
    }
    return render(request, 'stela/catalogo/update.html', context)


@access_required('038', stay_on_page=True)
def ciiu_delete(request, codigo):
    """
    Elimina un código CIIU (con validación de empresas e hijos).
    """
    ciiu = get_object_or_404(Ciiu, codigo=codigo)
    
    # Validar si tiene empresas asociadas
    empresas_count = Empresa.objects.filter(ciiu=ciiu).count()
    hijos_count = ciiu.hijos.count()
    
    if request.method == 'POST':
        # Verificar nuevamente antes de eliminar
        if Empresa.objects.filter(ciiu=ciiu).exists():
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

@access_required('008', stay_on_page=True)
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
    catalogo_id_param = request.GET.get('catalogo_id', '')  # Catálogo desde parámetro URL
    
    if request.method == 'POST':
        empresa_nit = request.POST.get('empresa')
        anio = request.POST.get('anio')  # Año para el período de estados financieros
        archivo = request.FILES.get('archivo')
        
        if not empresa_nit or not archivo:
            messages.error(request, 'Faltan datos requeridos')
            return redirect('catalogo_upload')
        
        try:
            # se cambio por el nuevo campo many to many
            empresa = get_object_or_404(Empresa.objects.filter(usuario=request.user), nit=empresa_nit)
            
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
                # Verificar si es la primera vez que se carga el catálogo (no hay mapeos previos)
                from stela.models.finanzas import MapeoCuentaLinea
                mapeos_previos = MapeoCuentaLinea.objects.filter(
                    cuenta__grupo__catalogo=catalogo
                ).count()
                
                # Mapear automáticamente cuentas a líneas de estado basándose en ratio_tag
                total_mapeadas = 0
                try:
                    from stela.services.mapeo_automatico import mapear_cuentas_por_bloques
                    resumen_mapeo = mapear_cuentas_por_bloques(catalogo)
                    total_mapeadas = sum(resumen_mapeo.values())
                    if errores:
                        messages.warning(request, f"Se procesaron {creados} cuentas, pero hubo {len(errores)} errores. {total_mapeadas} cuentas mapeadas automáticamente a líneas de estado.")
                    else:
                        messages.success(request, f"Catálogo cargado correctamente. {creados} cuentas procesadas y {total_mapeadas} cuentas mapeadas automáticamente a líneas de estado.")
                except ValueError as e:
                    # Si faltan líneas de estado, mostrar advertencia pero continuar
                    messages.warning(request, f"Catálogo cargado correctamente. {creados} cuentas procesadas. Advertencia: {str(e)}")
                except Exception as e:
                    # Si hay otro error en el mapeo, registrar pero no bloquear
                    messages.warning(request, f"Catálogo cargado correctamente. {creados} cuentas procesadas. Error en mapeo automático: {str(e)}")
                
                # Si es la primera vez (no había mapeos previos) y se crearon mapeos, mostrar paso 2.5
                # Si ya había mapeos o no se crearon nuevos, ir directo a estados financieros
                if mapeos_previos == 0 and total_mapeadas > 0:
                    # Primera vez con mapeos creados: ir al paso de mapeo (paso 2.5)
                    return redirect(f"{reverse('catalogo_upload')}?paso=2.5&empresa={empresa_nit}&catalogo_id={catalogo.id_catalogo}")
                else:
                    # Ya tiene mapeos o no se crearon: ir directo a estados financieros
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
    # se cambio por el nuevo campo many to many
    empresas = Empresa.objects.filter(usuario=request.user).distinct().order_by('razon_social')
    catalogo_id = request.GET.get('catalogo_id', '')
    
    # Si hay empresa en parámetro, verificar si ya tiene catálogo
    empresa_seleccionada = None
    if empresa_nit_param:
        try:
            # se cambio por el nuevo campo many to many
            empresa_seleccionada = get_object_or_404(Empresa.objects.filter(usuario=request.user), nit=empresa_nit_param)
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
    
    # Si hay catálogo_id, obtener el catálogo para el paso 3 o 2.5
    catalogo = None
    mapeos_existentes = 0
    # Usar catalogo_id_param si catalogo_id está vacío
    catalogo_id_final = catalogo_id or catalogo_id_param
    if catalogo_id_final:
        try:
            catalogo = Catalogo.objects.get(pk=catalogo_id_final, empresa__usuario=request.user)
            # Verificar si ya hay mapeos (para saber si mostrar paso 2.5)
            from stela.models.finanzas import MapeoCuentaLinea
            mapeos_existentes = MapeoCuentaLinea.objects.filter(
                cuenta__grupo__catalogo=catalogo
            ).count()
        except (Catalogo.DoesNotExist, ValueError):
            pass
    
    context = {
        'empresas_usuario': empresas,
        'paso': paso,
        'empresa_nit': empresa_nit_param or request.GET.get('empresa', ''),
        'catalogo_id': catalogo_id_final,
        'catalogo': catalogo,
        'tiene_catalogo': catalogo is not None,
        'tiene_mapeos': mapeos_existentes > 0,
        'num_mapeos': mapeos_existentes
    }
    return render(request, 'stela/catalogo/upload.html', context)


@access_required('009', stay_on_page=True)
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


@access_required('010', stay_on_page=True)
def catalogo_mapeo_cuentas(request, catalogo_id):
    """
    Vista para mapear cuentas a líneas de estado (para ratios).
    Pestaña oculta, no aparece en el menú principal.
    
    Permite mapeo manual mediante formulario y re-mapeo automático basado en bloques.
    """
    catalogo = get_object_or_404(Catalogo, pk=catalogo_id, empresa__usuario=request.user)
    
    # Si se solicita re-mapeo automático (parámetro GET)
    if request.GET.get('auto_mapear') == '1':
        try:
            from stela.services.mapeo_automatico import mapear_cuentas_por_bloques
            resumen_mapeo = mapear_cuentas_por_bloques(catalogo)
            total_mapeadas = sum(resumen_mapeo.values())
            messages.success(request, f'Mapeo automático completado. {total_mapeadas} cuentas mapeadas a líneas de estado.')
        except ValueError as e:
            messages.error(request, f'Error en mapeo automático: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error inesperado en mapeo automático: {str(e)}')
        # Redirigir para recargar el formulario con los nuevos mapeos
        return redirect(f"{reverse('catalogo_mapeo', args=[catalogo_id])}")
    
    if request.method == 'POST':
        form = MapeoCuentaForm(request.POST, catalogo=catalogo)
        if form.is_valid():
            from stela.models.finanzas import LineaEstado, MapeoCuentaLinea
            
            # Procesar cada campo del formulario (ahora puede tener múltiples cuentas)
            for field_name, cuentas_seleccionadas in form.cleaned_data.items():
                if field_name.startswith('linea_') and cuentas_seleccionadas:
                    clave_linea = field_name.replace('linea_', '')
                    try:
                        linea = LineaEstado.objects.get(clave=clave_linea)
                        
                        # Eliminar TODOS los mapeos existentes para esta línea en este catálogo
                        MapeoCuentaLinea.objects.filter(
                            linea=linea,
                            cuenta__grupo__catalogo=catalogo
                        ).delete()
                        
                        # Crear nuevos mapeos para cada cuenta seleccionada
                        cuentas_mapeadas = 0
                        for cuenta in cuentas_seleccionadas:
                            # Para UTILIDAD_NETA, el signo se determina por la naturaleza de la cuenta
                            # pero se aplicará correctamente en estado_dict
                            signo = 1  # Por defecto positivo
                            if clave_linea == 'UTILIDAD_NETA':
                                # El signo se ajustará en estado_dict según naturaleza y bloque
                                # Aquí solo guardamos 1, el cálculo real se hace en estado_dict
                                signo = 1
                            
                            MapeoCuentaLinea.objects.create(
                                cuenta=cuenta,
                                linea=linea,
                                signo=signo
                            )
                            cuentas_mapeadas += 1
                        
                        if cuentas_mapeadas > 0:
                            messages.info(request, f'{linea.nombre}: {cuentas_mapeadas} cuenta(s) mapeada(s)')
                    except LineaEstado.DoesNotExist:
                        pass
            
            messages.success(request, 'Mapeo de cuentas guardado correctamente.')
            return redirect('dashboard')
    else:
        # Si es la primera vez que se abre esta pantalla y no hay mapeos,
        # ejecutar mapeo automático silenciosamente
        from stela.models.finanzas import MapeoCuentaLinea
        mapeos_existentes = MapeoCuentaLinea.objects.filter(
            cuenta__grupo__catalogo=catalogo
        ).count()
        
        if mapeos_existentes == 0:
            # No hay mapeos, ejecutar automáticamente
            try:
                from stela.services.mapeo_automatico import mapear_cuentas_por_bloques
                resumen_mapeo = mapear_cuentas_por_bloques(catalogo)
                total_mapeadas = sum(resumen_mapeo.values())
                if total_mapeadas > 0:
                    messages.info(request, f'Mapeo automático ejecutado: {total_mapeadas} cuentas mapeadas según su ratio_tag.')
            except Exception as e:
                # Si falla el mapeo automático, continuar sin error
                pass
        
        form = MapeoCuentaForm(catalogo=catalogo)
    
    # Ejecutar mapeo automático si se solicita
    if request.GET.get('auto_mapear') == '1':
        try:
            from stela.services.mapeo_automatico import mapear_cuentas_por_bloques
            resumen_mapeo = mapear_cuentas_por_bloques(catalogo)
            total_mapeadas = sum(resumen_mapeo.values())
            if total_mapeadas > 0:
                messages.success(request, f'Mapeo automático ejecutado: {total_mapeadas} cuentas mapeadas según su ratio_tag, bg_bloque y er_bloque.')
                # Recargar el formulario con los nuevos mapeos
                form = MapeoCuentaForm(catalogo=catalogo)
        except Exception as e:
            messages.error(request, f'Error al ejecutar mapeo automático: {str(e)}')
    
    # Preparar información adicional de cuentas para el template
    # Crear un diccionario con información de grupo y naturaleza para cada cuenta
    cuentas_info = {}
    if catalogo:
        from stela.models.catalogo import Cuenta
        cuentas = Cuenta.objects.filter(grupo__catalogo=catalogo).select_related('grupo')
        for cuenta in cuentas:
            # Usar str(id_cuenta) como clave porque los valores del formulario son strings
            cuentas_info[str(cuenta.id_cuenta)] = {
                'grupo': cuenta.grupo.nombre,
                'naturaleza': cuenta.grupo.get_naturaleza_display() if hasattr(cuenta.grupo, 'get_naturaleza_display') else cuenta.grupo.naturaleza
            }
    
    context = {
        'form': form,
        'catalogo': catalogo,
        'titulo': 'Mapeo de Cuentas para Ratios',
        'cuentas_info': cuentas_info
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


@login_required
def get_ratios_api(request):
    """
    API que devuelve la lista de TODAS las definiciones de ratios
    (Esto es global, así que está bien como estaba).
    """
    try:
        ratios = RatioDef.objects.all().values(
            'clave', 'nombre', 'formula'
        )
        return JsonResponse(list(ratios), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_cuentas_api(request):
    """
    API que devuelve la lista de cuentas del catálogo
    DE LA EMPRESA ACTIVA (guardada en sesión).
    """
    try:
        # --- Obtener empresa activa de la sesión ---
        active_nit = request.session.get('active_company_nit')
        if not active_nit:
            return JsonResponse({'error': 'No hay empresa activa seleccionada'}, status=404)

        empresa = get_object_or_404(Empresa, nit=active_nit, usuario=request.user)
        # --- Fin de la obtención ---

        catalogo = Catalogo.objects.filter(empresa=empresa).first()
        if not catalogo:
            return JsonResponse([], safe=False)

        # Filtramos cuentas que pertenecen al catálogo de esa empresa
        cuentas = Cuenta.objects.filter(grupo__catalogo=catalogo).values(
            'id', 'codigo', 'nombre'
        )
        return JsonResponse(list(cuentas), safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_chart_data_api(request):
    """
    API que devuelve los datos (labels y datasets) para un conjunto
    de ratios o cuentas DE LA EMPRESA ACTIVA.
    """
    try:
        data_type = request.GET.get('type')
        item_ids = request.GET.getlist('ids')

        if not data_type or not item_ids:
            return JsonResponse({'error': 'Faltan parámetros type o ids'}, status=400)

        # --- Obtener empresa activa de la sesión ---
        active_nit = request.session.get('active_company_nit')
        if not active_nit:
            return JsonResponse({'error': 'No hay empresa activa seleccionada'}, status=404)

        empresa = get_object_or_404(Empresa, nit=active_nit, usuario=request.user)
        # --- Fin de la obtención ---

        periodos = Periodo.objects.filter(empresa=empresa).order_by('anio', 'mes')
        if not periodos.exists():
            return JsonResponse({'labels': [], 'datasets': []})  # No hay datos para graficar

        labels = [f"{p.anio}-{p.mes:02d}" if p.mes else str(p.anio) for p in periodos]
        datasets = []

        if data_type == 'ratios':
            # --- Lógica de Ratios (Completada) ---
            for ratio_clave in item_ids:
                try:
                    ratio_def = RatioDef.objects.get(clave=ratio_clave)
                    valores = []
                    for p in periodos:
                        # Buscamos el valor del ratio para ese período
                        r_res = ResultadoRatio.objects.filter(
                            empresa=empresa,
                            periodo=p,
                            ratio=ratio_def
                        ).first()
                        # Añadimos el valor o 0 si no existe
                        valores.append(float(r_res.valor) if r_res and r_res.valor is not None else 0)

                    datasets.append({
                        'label': ratio_def.nombre,
                        'data': valores,
                    })
                except RatioDef.DoesNotExist:
                    pass  # Ignora si la clave del ratio es incorrecta

        elif data_type == 'cuentas':
            # --- Lógica de Cuentas (Completada) ---
            for cuenta_id in item_ids:
                try:
                    cuenta = Cuenta.objects.get(id=cuenta_id)
                    # Validar que la cuenta pertenezca a la empresa activa
                    if cuenta.grupo.catalogo.empresa != empresa:
                        continue  # Esta cuenta no es de esta empresa

                    valores = []
                    for p in periodos:
                        # Buscamos el saldo de esa cuenta para ese período
                        bd = BalanceDetalle.objects.filter(
                            balance__empresa=empresa,
                            balance__periodo=p,
                            cuenta=cuenta
                        ).first()
                        # Añadimos el saldo o 0 si no existe
                        valores.append(float(bd.saldo) if bd and bd.saldo is not None else 0)

                    datasets.append({
                        'label': f"{cuenta.codigo} - {cuenta.nombre}",
                        'data': valores,
                    })
                except Cuenta.DoesNotExist:
                    pass  # Ignora si el ID de cuenta es incorrecto

        return JsonResponse({'labels': labels, 'datasets': datasets})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def set_active_company(request, empresa_nit):
    """
    Guarda el NIT de la empresa seleccionada en la sesión del usuario
    y lo redirige.
    """
    try:
        # 1. Verificar que la empresa existe y que el usuario tiene acceso a ella
        empresa = get_object_or_404(
            Empresa.objects.filter(usuario=request.user),
            nit=empresa_nit
        )

        # 2. Guardar el NIT en la sesión
        request.session['active_company_nit'] = empresa.nit
        messages.success(request, f'Empresa activa cambiada a: {empresa.razon_social}')

    except Exception as e:
        messages.error(request, 'No se pudo seleccionar la empresa.')

    # 3. Redirigir. 'HTTP_REFERER' lo devuelve a la página donde estaba.
    #    Usamos el dashboard como fallback.
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return HttpResponseRedirect(referer)
    return redirect('dashboard')