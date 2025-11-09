"""
Script de prueba para verificar que la generación de plantillas funcione correctamente.
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_financiero.settings')
django.setup()

from stela.services.plantillas import generar_plantilla_catalogo_excel, generar_plantilla_estados_excel
from stela.models.empresa import Empresa
from stela.models.catalogo import Catalogo

def main():
    print("=== PRUEBA DE GENERACIÓN DE PLANTILLAS ===\n")
    
    # Obtener primera empresa
    empresa = Empresa.objects.first()
    if not empresa:
        print("ERROR: No hay empresas en la base de datos")
        return
    
    print(f"Empresa: {empresa.razon_social}")
    
    # Obtener o crear catálogo
    catalogo = Catalogo.objects.filter(empresa=empresa).first()
    if not catalogo:
        print("ERROR: La empresa no tiene catálogo")
        return
    
    print(f"Catálogo ID: {catalogo.id_catalogo}\n")
    
    # Probar generación de plantilla de catálogo
    print("1. Generando plantilla de catálogo...")
    try:
        output_catalogo = generar_plantilla_catalogo_excel()
        print(f"   ✓ Plantilla de catálogo generada ({len(output_catalogo.getvalue())} bytes)")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    # Probar generación de plantilla de estados financieros
    print("2. Generando plantilla de estados financieros...")
    try:
        output_estados = generar_plantilla_estados_excel(catalogo)
        print(f"   ✓ Plantilla de estados financieros generada ({len(output_estados.getvalue())} bytes)")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    print("\n✓ TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")

if __name__ == '__main__':
    main()

