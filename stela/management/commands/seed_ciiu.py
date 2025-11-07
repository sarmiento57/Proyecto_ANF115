import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from stela.models.ciiu import Ciiu


class Command(BaseCommand):
    help = "Carga códigos CIIU desde el archivo CSV en stela/seeders/ciiu.csv"

    def handle(self, *args, **kwargs):
        # Ruta al archivo CSV
        csv_path = os.path.join(
            settings.BASE_DIR,
            'stela',
            'seeders',
            'ciiu.csv'
        )

        if not os.path.exists(csv_path):
            raise CommandError(f"El archivo {csv_path} no existe.")

        creados = 0
        actualizados = 0
        errores = []

        # Diccionario temporal para mapear códigos a objetos CIIU
        ciiu_dict = {}

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Primera pasada: crear todos los CIIU sin padre
            for row in reader:
                codigo = row['codigo'].strip()
                descripcion = row['descripcion'].strip()
                nivel = int(row['nivel'].strip())
                codigo_padre = row['codigo_padre'].strip() if row['codigo_padre'].strip() else None

                if not codigo or not descripcion:
                    errores.append(f"Fila con código o descripción vacía: {row}")
                    continue

                try:
                    ciiu, created = Ciiu.objects.get_or_create(
                        codigo=codigo,
                        defaults={
                            'descripcion': descripcion,
                            'nivel': nivel,
                            'padre': None  # Se asignará después
                        }
                    )
                    
                    if not created:
                        # Actualizar descripción y nivel si cambió
                        if ciiu.descripcion != descripcion or ciiu.nivel != nivel:
                            ciiu.descripcion = descripcion
                            ciiu.nivel = nivel
                            ciiu.save()
                            actualizados += 1
                        else:
                            creados -= 1  # Ya existía y no cambió
                    else:
                        creados += 1

                    ciiu_dict[codigo] = ciiu

                except Exception as e:
                    errores.append(f"Error al crear CIIU {codigo}: {e}")

        # Segunda pasada: asignar padres
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                codigo = row['codigo'].strip()
                codigo_padre = row['codigo_padre'].strip() if row['codigo_padre'].strip() else None

                if codigo_padre and codigo in ciiu_dict:
                    ciiu = ciiu_dict[codigo]
                    if codigo_padre in ciiu_dict:
                        padre = ciiu_dict[codigo_padre]
                        if ciiu.padre != padre:
                            ciiu.padre = padre
                            ciiu.save()
                    else:
                        errores.append(f"CIIU {codigo} tiene padre {codigo_padre} que no existe")

        # Resultado
        if errores:
            self.stdout.write(self.style.WARNING(f"Se encontraron {len(errores)} errores:"))
            for error in errores[:10]:  # Mostrar solo los primeros 10
                self.stdout.write(self.style.WARNING(f"  - {error}"))
            if len(errores) > 10:
                self.stdout.write(self.style.WARNING(f"  ... y {len(errores) - 10} más"))

        self.stdout.write(self.style.SUCCESS(
            f"CIIU cargados: {creados} creados, {actualizados} actualizados. Total en BD: {Ciiu.objects.count()}"
        ))


