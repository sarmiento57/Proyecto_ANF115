"""
Comando para corregir empresas con ciiu_id inválido
"""
from django.core.management.base import BaseCommand
from stela.models import Empresa, Ciiu
from django.db import connection


class Command(BaseCommand):
    help = "Corrige empresas que tienen ciiu_id='ciiu_id' (valor inválido)"

    def handle(self, *args, **options):
        # Primero verificar qué columnas tiene la tabla
        cursor = connection.cursor()
        cursor.execute("PRAGMA table_info(stela_empresa)")
        columnas = cursor.fetchall()
        
        # Buscar el nombre real de la columna ciiu
        columna_ciiu = None
        for col in columnas:
            if 'ciiu' in col[1].lower():
                columna_ciiu = col[1]
                break
        
        if not columna_ciiu:
            self.stdout.write(self.style.ERROR("No se encontró columna ciiu en stela_empresa"))
            return
        
        self.stdout.write(f"Columna encontrada: {columna_ciiu}")
        
        # Buscar empresas con valor inválido 'ciiu_id' o que no tengan un CIIU válido
        # Primero, obtener todos los códigos CIIU válidos
        ciiu_validos = list(Ciiu.objects.values_list('codigo', flat=True))
        
        if not ciiu_validos:
            self.stdout.write(self.style.ERROR(
                "⚠ No hay códigos CIIU en la base de datos.\n"
                "Ejecuta primero: python manage.py seed_ciiu"
            ))
            return
        
        # Buscar empresas cuyo ciiu_id no esté en la lista de válidos
        # También buscar específicamente el valor 'ciiu_id' que menciona el error
        try:
            # Obtener todas las empresas y verificar cuáles tienen ciiu inválido
            cursor.execute(f"SELECT nit, razon_social, {columna_ciiu} FROM stela_empresa")
            todas_empresas = cursor.fetchall()
            
            rows = []
            for row in todas_empresas:
                nit, razon_social, ciiu_valor = row
                # Verificar si el valor es 'ciiu_id' literal o no está en la lista de válidos
                if ciiu_valor == 'ciiu_id' or (ciiu_valor and ciiu_valor not in ciiu_validos):
                    rows.append(row)
                    self.stdout.write(f"  Encontrada empresa inválida: NIT={nit}, ciiu_valor='{ciiu_valor}'")
            
            # También buscar específicamente por el valor 'ciiu_id' usando ambos nombres posibles
            for nombre_col in [columna_ciiu, 'ciiu_id']:
                try:
                    cursor.execute(f"SELECT nit, razon_social, {nombre_col} FROM stela_empresa WHERE {nombre_col} = 'ciiu_id'")
                    rows_adicionales = cursor.fetchall()
                    for row in rows_adicionales:
                        if row not in rows:
                            rows.append(row)
                            self.stdout.write(f"  Encontrada (búsqueda directa): NIT={row[0]}, ciiu_valor='ciiu_id'")
                except:
                    pass
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error al consultar: {e}"))
            return

        if not rows:
            self.stdout.write(self.style.SUCCESS("✓ No hay empresas con ciiu_id inválido."))
            return

        self.stdout.write(self.style.WARNING(f"Encontradas {len(rows)} empresas con ciiu_id inválido:"))
        for row in rows:
            self.stdout.write(f"  - NIT: {row[0]}, Razón Social: {row[1]}")

        # Obtener un CIIU válido
        ciiu_valido = Ciiu.objects.first()
        if not ciiu_valido:
            self.stdout.write(self.style.ERROR(
                "⚠ No hay códigos CIIU en la base de datos.\n"
                "Ejecuta primero: python manage.py seed_ciiu"
            ))
            return

        self.stdout.write(f"\nUsando CIIU válido: {ciiu_valido.codigo} - {ciiu_valido.descripcion}")

        # Corregir usando SQL directo para evitar problemas con el ORM
        corregidas = 0
        for row in rows:
            nit = row[0]
            try:
                cursor.execute(f"UPDATE stela_empresa SET {columna_ciiu} = ? WHERE nit = ?", 
                             [ciiu_valido.codigo, nit])
                self.stdout.write(f"  ✓ Corregida: {row[1]} (NIT: {nit})")
                corregidas += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ Error al corregir {nit}: {e}"))

        connection.commit()
        self.stdout.write(self.style.SUCCESS(f"\n✓ {corregidas} empresas corregidas exitosamente."))
        self.stdout.write("Ahora puedes ejecutar: python manage.py migrate")

