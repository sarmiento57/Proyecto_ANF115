from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.conf import settings  # Importar settings
import os
import re  # Importar regex para reemplazo robusto


class Command(BaseCommand):
    help = 'Ejecuta un archivo SQL para poblar la base de datos, ignorando duplicados.'

    def handle(self, *args, **kwargs):

        # --- SOLUCIÓN 1: Ruta de archivo robusta ---
        # Usamos settings.BASE_DIR para construir una ruta absoluta y segura
        # Asumiendo que 'accounts' está en la raíz del proyecto, junto a 'manage.py'
        sql_path = os.path.join(settings.BASE_DIR, 'accounts', 'sql', 'sqlitePruebas.sql')

        if not os.path.exists(sql_path):
            self.stdout.write(self.style.ERROR(f"Archivo SQL no encontrado en: {sql_path}"))
            return

        self.stdout.write(self.style.WARNING(f"Ejecutando script SQL desde: {sql_path}"))

        try:
            with open(sql_path, 'r', encoding='utf-8') as f:
                sql = f.read()

            # --- SOLUCIÓN 2: Pre-procesar el script ---
            # Aplicamos tu lógica de 'INSERT OR IGNORE' a todo el script ANTES de ejecutarlo.
            # Usamos regex (re.sub) para ser más robustos (ignora mayúsculas/minúsculas y espacios extra)
            sql_con_ignore = re.sub(
                r'\bINSERT\s+INTO\b',
                'INSERT OR IGNORE INTO',
                sql,
                flags=re.IGNORECASE
            )

            with connection.cursor() as cursor:
                # Desactivar validación de claves foráneas (buena idea para SQLite)
                cursor.execute("PRAGMA foreign_keys = OFF;")

                # --- SOLUCIÓN 3: Usar executescript() ---
                # Esta es la función correcta para ejecutar un bloque de SQL
                # con múltiples sentencias. Maneja transacciones y ';' correctamente.
                with transaction.atomic():
                    cursor.executescript(sql_con_ignore)

                # Reactivar las claves foráneas
                cursor.execute("PRAGMA foreign_keys = ON;")

            self.stdout.write(self.style.SUCCESS(
                "Script SQL ejecutado con éxito. Los duplicados fueron ignorados."
            ))
            # Nota: executescript() no devuelve 'rowcount', por lo que
            # no podemos contar inserciones fácilmente, pero este mensaje es más preciso.

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error al ejecutar el script SQL: {e}"))