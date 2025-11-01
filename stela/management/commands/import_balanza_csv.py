import csv
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from stela.models.empresa import Empresa
from stela.models.finanzas import Periodo, Balance, BalanceDetalle
from stela.models.catalogo import Catalogo, GrupoCuenta, Cuenta
from stela.services.estados import recalcular_saldos_detalle

"""
CSV esperado: codigo,nombre,grupo,naturaleza(A/L/P/I/G),debe,haber
"""

class Command(BaseCommand):
    help = "Importa una balanza/estado por período desde CSV y recalcula saldos"

    def add_arguments(self, p):
        p.add_argument('--nit', help='NIT de la empresa (ej. 0614...)')
        p.add_argument('--empresa_id', type=int, help='ID (pk) de la empresa como alternativa al NIT')
        p.add_argument('--anio', type=int, required=True)
        p.add_argument('--mes', type=int)
        p.add_argument('--tipo', choices=['BAL','RES'], default='RES')
        p.add_argument('--file', required=True)

    def handle(self, *a, **o):
        # --- Empresa por NIT o por ID ---
        emp = None
        if o.get('empresa_id'):
            try:
                emp = Empresa.objects.get(pk=o['empresa_id'])
            except Empresa.DoesNotExist:
                raise CommandError(f"Empresa con id={o['empresa_id']} no existe")
        elif o.get('nit'):
            try:
                emp = Empresa.objects.get(nit=o['nit'])
            except Empresa.DoesNotExist:
                raise CommandError(f"Empresa con nit={o['nit']} no existe")
        else:
            raise CommandError("Debes pasar --nit o --empresa_id")

        anio = o['anio']
        mes = o.get('mes')
        tipo = o['tipo']
        file_path = o['file']

        # --- Periodo / Balance / Catalogo por empresa ---
        per, _ = Periodo.objects.get_or_create(empresa=emp, anio=anio, mes=mes)
        bal, _ = Balance.objects.get_or_create(empresa=emp, periodo=per, tipo_balance=tipo)
        cat, _ = Catalogo.objects.get_or_create(empresa=emp, anio_catalogo=anio)

        # --- Importación ---
        creados = 0
        with open(file_path, newline='', encoding='utf-8') as f:
            rd = csv.DictReader(f)
            for i, row in enumerate(rd, start=1):
                try:
                    codigo = row['codigo'].strip()
                    nombre = row['nombre'].strip()
                    grupo_nombre = row['grupo'].strip()
                    nat = row['naturaleza'].strip().upper()  # A/L/P/I/G
                    debe = Decimal(row.get('debe','0') or '0')
                    haber = Decimal(row.get('haber','0') or '0')
                except KeyError as e:
                    raise CommandError(f"Columna faltante en fila {i}: {e}")

                grupo, _ = GrupoCuenta.objects.get_or_create(
                    catalogo=cat, nombre=grupo_nombre,
                    defaults={'naturaleza': nat}
                )
                # Si ya existía el grupo pero sin naturaleza, intenta setearla
                if not grupo.naturaleza:
                    grupo.naturaleza = nat
                    grupo.save(update_fields=['naturaleza'])

                cta, _ = Cuenta.objects.get_or_create(
                    grupo=grupo, codigo=codigo,
                    defaults={'nombre': nombre, 'aparece_en_balance': True}
                )
                # Actualiza nombre si cambió (útil en cargas sucesivas)
                if cta.nombre != nombre:
                    cta.nombre = nombre
                    cta.save(update_fields=['nombre'])

                BalanceDetalle.objects.create(
                    balance=bal, cuenta=cta, debe=debe, haber=haber
                )
                creados += 1

        # --- Recalcular saldos ---
        recalcular_saldos_detalle(bal)

        self.stdout.write(self.style.SUCCESS(
            f"OK: Empresa {emp.nit} · {tipo} {anio}{('-'+str(mes)) if mes else ''} · filas importadas: {creados}"
        ))
