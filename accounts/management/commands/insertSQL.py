from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.conf import settings
import os
import re

class Command(BaseCommand):
    help = 'Ejecuta un archivo SQL en MySQL, ignorando duplicados.'

    def handle(self, *args, **kwargs):
        sql_path = os.path.join(settings.BASE_DIR, 'accounts', 'sql', 'MySQL.sql')

        if not os.path.exists(sql_path):
            self.stdout.write(self.style.ERROR(f"Archivo SQL no encontrado en: {sql_path}"))
            return

        self.stdout.write(self.style.WARNING(f"Ejecutando script SQL desde: {sql_path}"))

        try:
            with open(sql_path, 'r', encoding='utf-8') as f:
                sql = f.read()

            # Reemplazar 'INSERT INTO' por 'INSERT IGNORE INTO' para evitar duplicados
            sql_con_ignore = re.sub(
                r'\bINSERT\s+INTO\b',
                'INSERT IGNORE INTO',
                sql,
                flags=re.IGNORECASE
            )

            # Separar el script en sentencias individuales
            statements = [stmt.strip() for stmt in sql_con_ignore.split(';') if stmt.strip()]

            with connection.cursor() as cursor:
                with transaction.atomic():
                    for stmt in statements:
                        cursor.execute(stmt)

            self.stdout.write(self.style.SUCCESS("Script SQL ejecutado con éxito en MySQL."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error al ejecutar el script SQL: {e}"))
