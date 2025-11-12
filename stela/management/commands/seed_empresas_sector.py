"""
Comando de Django para generar empresas con datos reales en sectores
que tienen ratios por sector definidos, junto con sus estados financieros.

Basado en el script temp/scripts/generar_excel_5_periodos.py
"""
import os
import sys
import json
import random
from decimal import Decimal
from pathlib import Path
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

# Importar modelos
from stela.models.empresa import Empresa
from stela.models.ciiu import Ciiu
from stela.models.catalogo import Catalogo, GrupoCuenta, Cuenta
from stela.models.finanzas import Periodo, Balance, BalanceDetalle
from stela.services.plantillas import CUENTAS_BASE
from stela.services.ratios import calcular_y_guardar_ratios
from stela.services.estados import recalcular_saldos_detalle


# Cargar ratios sector desde JSON
RATIOS_SECTOR_FILE = Path(__file__).parent.parent.parent / 'seeders' / 'ratios_sector.json'


def cargar_ratios_sector():
    """Carga ratios por sector desde archivo JSON"""
    if RATIOS_SECTOR_FILE.exists():
        with open(RATIOS_SECTOR_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def obtener_valores_base_ajustados(ratios_sector):
    """
    Genera valores base ajustados para que los ratios calculados
    se acerquen a los valores de referencia del sector.
    
    Args:
        ratios_sector: Diccionario con ratios de referencia del sector
        
    Returns:
        Diccionario con valores iniciales ajustados
    """
    # Valores base (pueden ajustarse según el sector)
    liquidez = ratios_sector.get('LIQUIDEZ_CORRIENTE', 1.5)
    endeudamiento = ratios_sector.get('ENDEUDAMIENTO', 0.6)
    margen_neto = ratios_sector.get('MARGEN_NETO', 0.075)
    roa = ratios_sector.get('ROA', 0.065)
    roe = ratios_sector.get('ROE', 0.125)
    rotacion = ratios_sector.get('ROTACION_ACTIVOS', 1.15)
    razon_activos_corrientes = ratios_sector.get('RAZON_ACTIVOS_CORRIENTES', 0.20)
    razon_patrimonio = ratios_sector.get('RAZON_PATRIMONIO', 0.30)
    
    # Calcular valores base que generen estos ratios
    # Asumimos un tamaño de empresa (activos totales)
    total_activo_base = Decimal('1000000')  # 1 millón base
    
    # Activo corriente basado en razón
    activo_corriente = total_activo_base * Decimal(str(razon_activos_corrientes))
    
    # Pasivo corriente basado en liquidez
    pasivo_corriente = activo_corriente / Decimal(str(liquidez))
    
    # Patrimonio basado en razón
    patrimonio_total = total_activo_base * Decimal(str(razon_patrimonio))
    
    # Pasivo total (endeudamiento)
    pasivo_total = total_activo_base * Decimal(str(endeudamiento))
    pasivo_no_corriente = pasivo_total - pasivo_corriente
    
    # Activo no corriente
    activo_no_corriente = total_activo_base - activo_corriente
    
    # Ventas basadas en rotación
    ventas_netas = total_activo_base * Decimal(str(rotacion))
    
    # Utilidad neta basada en ROA
    utilidad_neta = total_activo_base * Decimal(str(roa))
    
    # Ajustar si margen neto no coincide
    if ventas_netas > 0:
        utilidad_esperada_margen = ventas_netas * Decimal(str(margen_neto))
        # Usar el promedio de ambos
        utilidad_neta = (utilidad_neta + utilidad_esperada_margen) / Decimal('2')
    
    # Valores base ajustados
    valores = {
        # Activos Corrientes
        '1101': {'debe': int(activo_corriente * Decimal('0.15')), 'haber': 0},  # Caja
        '1102': {'debe': int(activo_corriente * Decimal('0.50')), 'haber': 0},  # Bancos
        '1103': {'debe': int(activo_corriente * Decimal('0.10')), 'haber': 0},  # Equivalentes
        '1201': {'debe': int(activo_corriente * Decimal('0.20')), 'haber': 0},  # Cuentas por Cobrar
        '1202': {'debe': 0, 'haber': int(activo_corriente * Decimal('0.02'))},  # Estimación
        '1301': {'debe': int(activo_corriente * Decimal('0.05')), 'haber': 0},  # Inventarios
        '1401': {'debe': 0, 'haber': 0},  # Otros Activos Corrientes
        
        # Activos No Corrientes
        '1501': {'debe': int(activo_no_corriente * Decimal('0.85')), 'haber': 0},  # PPE
        '1502': {'debe': 0, 'haber': int(activo_no_corriente * Decimal('0.20'))},  # Depreciación
        '1601': {'debe': int(activo_no_corriente * Decimal('0.10')), 'haber': 0},  # Intangibles
        '1602': {'debe': 0, 'haber': int(activo_no_corriente * Decimal('0.02'))},  # Amortización
        '1701': {'debe': int(activo_no_corriente * Decimal('0.05')), 'haber': 0},  # Otros
        
        # Pasivos Corrientes
        '2101': {'debe': 0, 'haber': int(pasivo_corriente * Decimal('0.40'))},  # Cuentas por Pagar
        '2102': {'debe': 0, 'haber': int(pasivo_corriente * Decimal('0.20'))},  # Otras Cuentas
        '2103': {'debe': 0, 'haber': int(pasivo_corriente * Decimal('0.15'))},  # Porción Corriente
        '2104': {'debe': 0, 'haber': int(pasivo_corriente * Decimal('0.25'))},  # Documentos
        '5701': {'debe': 0, 'haber': 0},  # Servicio de Deuda
        
        # Pasivos No Corrientes
        '2501': {'debe': 0, 'haber': int(pasivo_no_corriente)},  # Préstamos Largo Plazo
        
        # Patrimonio
        '3101': {'debe': 0, 'haber': int(patrimonio_total * Decimal('0.70'))},  # Capital Social
        '3102': {'debe': 0, 'haber': int(patrimonio_total * Decimal('0.10'))},  # Reservas
        '3103': {'debe': 0, 'haber': 0},  # Utilidades Retenidas (se calculará)
        
        # Estado de Resultados
        '4101': {'debe': 0, 'haber': int(ventas_netas)},  # Ventas
        '4102': {'debe': int(ventas_netas * Decimal('0.02')), 'haber': 0},  # Descuentos
        '4103': {'debe': int(ventas_netas * Decimal('0.01')), 'haber': 0},  # Devoluciones
        '5101': {'debe': int(ventas_netas * Decimal('0.55')), 'haber': 0},  # Costo de Ventas
        '5102': {'debe': 0, 'haber': 0},  # Devoluciones sobre Compras
        '5103': {'debe': 0, 'haber': 0},  # Compras (se ajusta con costo)
        '5201': {'debe': int(ventas_netas * Decimal('0.10')), 'haber': 0},  # Gastos Operativos
        '5202': {'debe': int(ventas_netas * Decimal('0.08')), 'haber': 0},  # Gastos de Venta
        '5203': {'debe': int(ventas_netas * Decimal('0.05')), 'haber': 0},  # Gastos Generales
        '4301': {'debe': 0, 'haber': int(ventas_netas * Decimal('0.02'))},  # Otros Ingresos
        '5301': {'debe': int(ventas_netas * Decimal('0.01')), 'haber': 0},  # Otros Gastos
        '5401': {'debe': int(pasivo_total * Decimal('0.08')), 'haber': 0},  # Gasto Financiero
        '5501': {'debe': 0, 'haber': 0},  # Impuesto (se calculará)
        '5601': {'debe': int(activo_no_corriente * Decimal('0.05')), 'haber': 0},  # Depreciación
        '5602': {'debe': int(activo_no_corriente * Decimal('0.02')), 'haber': 0},  # Amortización
    }
    
    # Calcular utilidades retenidas para cuadrar balance
    total_activos = sum(v['debe'] - v['haber'] for k, v in valores.items() 
                       if k in ['1101', '1102', '1103', '1201', '1202', '1301', '1401', 
                               '1501', '1502', '1601', '1602', '1701'])
    total_pasivos = sum(v['haber'] - v['debe'] for k, v in valores.items() 
                       if k in ['2101', '2102', '2103', '2104', '5701', '2501'])
    patrimonio_sin_utilidades = sum(v['haber'] - v['debe'] for k, v in valores.items() 
                                   if k in ['3101', '3102'])
    utilidades_retenidas = total_activos - total_pasivos - patrimonio_sin_utilidades
    valores['3103'] = {'debe': 0, 'haber': max(0, int(utilidades_retenidas))}
    
    return valores


def calcular_valores_periodo(valores_base, periodo, total_periodos=5):
    """
    Calcula valores para un periodo específico con cambios consistentes.
    Similar a generar_excel_5_periodos.py
    """
    factores_crecimiento = {
        '1101': 1.10, '1102': 1.10, '1103': 1.10,
        '1201': 1.10, '1301': 1.10, '1401': 1.10,
        '1501': 1.0,
        '1502': 1.0,
        '1601': 1.0,
        '1602': 1.0,
        '1701': 1.08,
        '2101': 1.08, '2102': 1.08, '2103': 1.08, '2104': 1.08, '5701': 1.08,
        '2501': 1.05,
        '3101': 1.0,
        '3102': 1.0,
        '3103': 1.0,
        '4101': 1.12,
        '4102': 1.12,
        '4103': 1.12,
        '5101': 1.10, '5102': 1.10, '5103': 1.10,
        '5201': 1.10, '5202': 1.10, '5203': 1.10,
        '5401': 1.10, '5301': 1.10,
        '4301': 1.08,
        '5501': 1.10,
        '5601': 1.0,
        '5602': 1.0,
    }
    
    valores_periodo = {}
    
    for codigo, valores in valores_base.items():
        debe_base = valores['debe']
        haber_base = valores['haber']
        factor = factores_crecimiento.get(codigo, 1.08)
        
        if periodo == 0:
            valores_periodo[codigo] = {'debe': debe_base, 'haber': haber_base}
        else:
            if codigo == '1502':
                # Depreciación acumulada
                dep_anual = int(valores_base.get('5601', {}).get('debe', 25000))
                valores_periodo[codigo] = {
                    'debe': 0,
                    'haber': valores_base['1502']['haber'] + (dep_anual * periodo)
                }
            elif codigo == '1602':
                # Amortización acumulada
                am_anual = int(valores_base.get('5602', {}).get('debe', 10000))
                valores_periodo[codigo] = {
                    'debe': 0,
                    'haber': valores_base['1602']['haber'] + (am_anual * periodo)
                }
            elif codigo == '3103':
                continue  # Se calculará después
            elif codigo == '1501':
                inversiones_periodos = periodo // 2
                if inversiones_periodos > 0:
                    valores_periodo[codigo] = {
                        'debe': int(debe_base * (1.05 ** inversiones_periodos)),
                        'haber': haber_base
                    }
                else:
                    valores_periodo[codigo] = {'debe': debe_base, 'haber': haber_base}
            else:
                nuevo_debe = int(debe_base * (factor ** periodo)) if debe_base > 0 else 0
                nuevo_haber = int(haber_base * (factor ** periodo)) if haber_base > 0 else 0
                valores_periodo[codigo] = {'debe': nuevo_debe, 'haber': nuevo_haber}
    
    # Calcular utilidades retenidas para cuadrar
    activos_cuentas = ['1101', '1102', '1103', '1201', '1202', '1301', '1401', 
                      '1501', '1502', '1601', '1602', '1701']
    total_activos = sum(valores_periodo.get(c, {}).get('debe', 0) - 
                       valores_periodo.get(c, {}).get('haber', 0) 
                       for c in activos_cuentas)
    
    pasivos_cuentas = ['2101', '2102', '2103', '2104', '5701', '2501']
    total_pasivos = sum(valores_periodo.get(c, {}).get('haber', 0) - 
                      valores_periodo.get(c, {}).get('debe', 0) 
                      for c in pasivos_cuentas)
    
    patrimonio_cuentas = ['3101', '3102']
    total_patrimonio_sin_utilidades = sum(valores_periodo.get(c, {}).get('haber', 0) - 
                                         valores_periodo.get(c, {}).get('debe', 0) 
                                         for c in patrimonio_cuentas)
    
    utilidades_retenidas = total_activos - total_pasivos - total_patrimonio_sin_utilidades
    valores_periodo['3103'] = {'debe': 0, 'haber': max(0, int(utilidades_retenidas))}
    
    return valores_periodo


def crear_catalogo_por_defecto(empresa):
    """Crea un catálogo por defecto usando CUENTAS_BASE"""
    catalogo, created = Catalogo.objects.get_or_create(empresa=empresa)
    
    if not created:
        total_cuentas = Cuenta.objects.filter(grupo__catalogo=catalogo).count()
        if total_cuentas > 0:
            return catalogo
    
    grupos_dict = {}
    for cuenta_data in CUENTAS_BASE:
        grupo_nombre = cuenta_data['grupo']
        if grupo_nombre not in grupos_dict:
            grupos_dict[grupo_nombre] = []
        grupos_dict[grupo_nombre].append(cuenta_data)
    
    for grupo_nombre, cuentas_data in grupos_dict.items():
        naturaleza = cuentas_data[0]['naturaleza']
        grupo, _ = GrupoCuenta.objects.get_or_create(
            catalogo=catalogo,
            nombre=grupo_nombre,
            defaults={'naturaleza': naturaleza}
        )
        
        for cuenta_data in cuentas_data:
            Cuenta.objects.get_or_create(
                grupo=grupo,
                codigo=cuenta_data['codigo'],
                defaults={
                    'nombre': cuenta_data['nombre'],
                    'aparece_en_balance': True,
                    'bg_bloque': cuenta_data.get('bg_bloque', '') or None,
                    'er_bloque': cuenta_data.get('er_bloque', '') or None,
                    'ratio_tag': cuenta_data.get('ratio_tag', '') or None
                }
            )
    
    return catalogo


def generar_estados_financieros(empresa, catalogo, ratios_sector, anio_inicio=2020, num_periodos=5):
    """
    Genera estados financieros para múltiples períodos
    """
    valores_base = obtener_valores_base_ajustados(ratios_sector)
    periodos_creados = []
    
    for periodo_idx in range(num_periodos):
        anio = anio_inicio + periodo_idx
        valores_periodo = calcular_valores_periodo(valores_base, periodo_idx, num_periodos)
        
        # Crear período
        periodo, _ = Periodo.objects.get_or_create(
            empresa=empresa,
            anio=anio,
            mes=None
        )
        periodos_creados.append(periodo)
        
        # Crear balances
        balance_bal, _ = Balance.objects.get_or_create(
            empresa=empresa,
            periodo=periodo,
            tipo_balance='BAL'
        )
        
        balance_res, _ = Balance.objects.get_or_create(
            empresa=empresa,
            periodo=periodo,
            tipo_balance='RES'
        )
        
        # Obtener cuentas del catálogo
        cuentas = Cuenta.objects.filter(grupo__catalogo=catalogo)
        cuentas_dict = {c.codigo: c for c in cuentas}
        
        # Crear detalles de balance
        for codigo, valores in valores_periodo.items():
            if codigo in cuentas_dict:
                cuenta = cuentas_dict[codigo]
                
                # Determinar a qué balance pertenece
                if cuenta.grupo.naturaleza in ('Activo', 'Pasivo', 'Patrimonio'):
                    balance = balance_bal
                else:
                    balance = balance_res
                
                # Crear o actualizar detalle
                detalle, _ = BalanceDetalle.objects.get_or_create(
                    balance=balance,
                    cuenta=cuenta,
                    defaults={
                        'debe': Decimal(str(valores['debe'])),
                        'haber': Decimal(str(valores['haber'])),
                        'saldo': Decimal('0')
                    }
                )
                detalle.debe = Decimal(str(valores['debe']))
                detalle.haber = Decimal(str(valores['haber']))
                detalle.save()
        
        # Recalcular saldos
        recalcular_saldos_detalle(balance_bal)
        recalcular_saldos_detalle(balance_res)
        
        # Calcular ratios automáticamente
        calcular_y_guardar_ratios(empresa, periodo, tipo_estado='BAL')
        calcular_y_guardar_ratios(empresa, periodo, tipo_estado='RES')
    
    return periodos_creados


class Command(BaseCommand):
    help = "Genera empresas con datos reales en sectores con ratios definidos, junto con estados financieros"

    def add_arguments(self, parser):
        parser.add_argument(
            '--ciiu',
            type=str,
            help='Código CIIU específico para crear una empresa (opcional)'
        )
        parser.add_argument(
            '--num-empresas',
            type=int,
            default=1,
            help='Número de empresas a crear por CIIU (default: 1)'
        )
        parser.add_argument(
            '--anio-inicio',
            type=int,
            default=2020,
            help='Año inicial para los períodos (default: 2020)'
        )
        parser.add_argument(
            '--num-periodos',
            type=int,
            default=5,
            help='Número de períodos a generar (default: 5)'
        )

    def handle(self, *args, **options):
        ratios_sector = cargar_ratios_sector()
        
        if not ratios_sector:
            self.stdout.write(self.style.ERROR('No se encontró el archivo ratios_sector.json'))
            return
        
        # Obtener CIIU únicos del JSON
        ciiu_codigos = list(ratios_sector.keys())
        
        if options['ciiu']:
            if options['ciiu'] not in ciiu_codigos:
                self.stdout.write(self.style.ERROR(f'CIIU {options["ciiu"]} no está en ratios_sector.json'))
                return
            ciiu_codigos = [options['ciiu']]
        
        # Obtener o crear usuario por defecto
        usuario, _ = User.objects.get_or_create(
            username='seeder_user',
            defaults={
                'email': 'seeder@stela.com',
                'first_name': 'Seeder',
                'last_name': 'User',
                'is_active': True
            }
        )
        
        num_empresas_por_ciiu = options['num_empresas']
        anio_inicio = options['anio_inicio']
        num_periodos = options['num_periodos']
        
        empresas_creadas = []
        
        with transaction.atomic():
            for ciiu_codigo in ciiu_codigos:
                try:
                    ciiu = Ciiu.objects.get(codigo=ciiu_codigo)
                except Ciiu.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'CIIU {ciiu_codigo} no existe en la BD, saltando...'))
                    continue
                
                ratios_ciiu = ratios_sector[ciiu_codigo]
                
                for i in range(num_empresas_por_ciiu):
                    # Generar datos únicos para la empresa
                    nit_base = f"{random.randint(1000, 9999)}-{random.randint(100000, 999999)}-{random.randint(10, 99)}-{random.randint(1, 9)}"
                    nrc_base = f"{random.randint(1000000, 9999999)}"
                    
                    # Verificar que no exista
                    while Empresa.objects.filter(nit=nit_base).exists():
                        nit_base = f"{random.randint(1000, 9999)}-{random.randint(100000, 999999)}-{random.randint(10, 99)}-{random.randint(1, 9)}"
                    
                    while Empresa.objects.filter(nrc=nrc_base).exists():
                        nrc_base = f"{random.randint(1000000, 9999999)}"
                    
                    razon_social = f"Empresa {ciiu.descripcion[:20]} {i+1}"
                    if num_empresas_por_ciiu == 1:
                        razon_social = f"Empresa {ciiu.descripcion[:30]}"
                    
                    # Crear empresa
                    empresa = Empresa.objects.create(
                        nit=nit_base,
                        ciiu=ciiu,
                        nrc=nrc_base,
                        razon_social=razon_social,
                        direccion=f"Dirección {random.randint(1, 100)}, San Salvador",
                        telefono=f"{random.randint(2000, 7999)}-{random.randint(1000, 9999)}",
                        email=f"empresa{nit_base.replace('-', '')}@stela.com"
                    )
                    empresa.usuario.add(usuario)
                    
                    # Crear catálogo
                    catalogo = crear_catalogo_por_defecto(empresa)
                    
                    # Generar estados financieros
                    periodos = generar_estados_financieros(
                        empresa, catalogo, ratios_ciiu, anio_inicio, num_periodos
                    )
                    
                    empresas_creadas.append({
                        'empresa': empresa,
                        'periodos': periodos,
                        'ciiu': ciiu
                    })
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Empresa creada: {empresa.razon_social} (NIT: {empresa.nit}, '
                            f'CIIU: {ciiu.codigo}) - {len(periodos)} períodos generados'
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n=== RESUMEN ===\n'
                f'Empresas creadas: {len(empresas_creadas)}\n'
                f'Períodos por empresa: {num_periodos}\n'
                f'Año inicio: {anio_inicio}\n'
            )
        )

