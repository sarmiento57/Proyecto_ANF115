from django.core.management.base import BaseCommand
from django.db import connection
import os

class Command(BaseCommand):
    help = 'Ejecuta un archivo SQL sin importar que base de datos este configurada en settings.py.'

    def handle(self, *args, **kwargs):
        # Ruta del archivo .sql
        sql_path = os.path.join('accounts', 'sql', 'sqlitePruebas.sql') # cambiar luego al mysql

        if not os.path.exists(sql_path):
            self.stdout.write(self.style.ERROR(f"Archivo SQL no encontrado: {sql_path}"))
            return

        self.stdout.write(self.style.WARNING(f"Ejecutando script SQL desde: {sql_path}"))

        try:
            with open(sql_path, 'r', encoding='utf-8') as f:
                sql = f.read()

            # Conexión directa a la BD actual
            with connection.cursor() as cursor:
                for statement in sql.split(';'):
                    stmt = statement.strip()
                    if stmt:
                        cursor.execute(stmt)

            self.stdout.write(self.style.SUCCESS("Datos insertados correctamente desde el archivo SQL."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error al ejecutar el script SQL: {e}"))
