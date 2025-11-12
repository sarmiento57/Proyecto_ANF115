import json
from pathlib import Path
from decimal import Decimal
from django.conf import settings

def cargar_ratios_sector():
    """
    Carga ratios por sector desde archivo JSON estático.
    
    Returns:
        dict: {CIIU_CODE: {RATIO_CLAVE: valor, ...}, ...}
        Ejemplo: {"0111": {"LIQUIDEZ_CORRIENTE": 1.5, "ENDEUDAMIENTO": 0.6}}
    """
    ratios_file = Path(__file__).parent.parent / 'seeders' / 'ratios_sector.json'
    
    if not ratios_file.exists():
        return {}
    
    try:
        with open(ratios_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Convertir valores a Decimal para consistencia
            result = {}
            for ciiu_code, ratios in data.items():
                result[ciiu_code] = {
                    ratio_clave: Decimal(str(valor))
                    for ratio_clave, valor in ratios.items()
                }
            return result
    except (json.JSONDecodeError, ValueError, IOError) as e:
        return {}

def obtener_ratio_sector(ciiu_codigo, ratio_clave):
    """
    Obtiene el valor de referencia de un ratio para un sector específico.
    
    Args:
        ciiu_codigo: Código CIIU del sector
        ratio_clave: Clave del ratio (ej: 'LIQUIDEZ_CORRIENTE')
        
    Returns:
        Decimal o None: Valor del parámetro del sector, o None si no existe
    """
    ratios = cargar_ratios_sector()
    return ratios.get(ciiu_codigo, {}).get(ratio_clave)

def comparar_ratio_con_sector(valor_empresa, valor_sector, ratio_clave):
    """
    Compara el valor de un ratio de la empresa con el parámetro del sector.
    
    Args:
        valor_empresa: Valor del ratio de la empresa (Decimal o None)
        valor_sector: Valor del parámetro del sector (Decimal o None)
        ratio_clave: Clave del ratio para determinar si mayor o menor es mejor
        
    Returns:
        str: 'CUMPLE' si cumple, 'NO_CUMPLE' si no cumple, 'NA' si no hay parámetro
    """
    if valor_empresa is None or valor_sector is None:
        return 'NA'
    
    # Ratios donde menor es mejor (ENDEUDAMIENTO)
    ratios_menor_mejor = ['ENDEUDAMIENTO']
    
    if ratio_clave in ratios_menor_mejor:
        # Para estos ratios, cumple si valor_empresa <= valor_sector
        if valor_empresa <= valor_sector:
            return 'CUMPLE'
        else:
            return 'NO_CUMPLE'
    else:
        # Para el resto, mayor es mejor (LIQUIDEZ_CORRIENTE, MARGEN_NETO, ROA, ROE, etc.)
        if valor_empresa >= valor_sector:
            return 'CUMPLE'
        else:
            return 'NO_CUMPLE'

def obtener_comparacion_sector(empresa, ratios_empresa):
    """
    Obtiene la comparación de todos los ratios de la empresa con los parámetros del sector.
    
    Args:
        empresa: Instancia de Empresa
        ratios_empresa: Lista de diccionarios con {'clave': str, 'nombre': str, 'valor': Decimal}
        
    Returns:
        list: Lista de diccionarios con información de comparación
    """
    if not empresa.ciiu:
        return []
    
    ciiu_codigo = empresa.ciiu.codigo
    ratios_sector = cargar_ratios_sector()
    sector_ratios = ratios_sector.get(ciiu_codigo, {})
    
    resultado = []
    for r in ratios_empresa:
        ratio_clave = r['clave']
        valor_sector = sector_ratios.get(ratio_clave)
        valor_empresa = r.get('valor')
        
        semaforo = comparar_ratio_con_sector(valor_empresa, valor_sector, ratio_clave)
        
        resultado.append({
            **r,
            'valor_sector': valor_sector,
            'semaforo_sector': semaforo
        })
    
    return resultado

