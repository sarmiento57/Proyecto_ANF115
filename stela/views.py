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


# @access_required('010')
def dashboard(request):
    return render(request, "dashboard/dashboard.html")


def tools(request):
    return render(request, "tools/tools.html")


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
        col_mes = next((c for c in df.columns if "mes" in c or "fecha" in c), None)
        col_valor = next(
            (c for c in df.columns if "valor" in c or "monto" in c or "venta" in c), None
        )

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
                f"Ventas cargadas o guardadas correctamente para la empresa {empresa_seleccionada.razon_social}.",
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
