from django.db import connection, transaction

from .models import ConsultaSQL


class ConsultaNoDisponible(Exception):
    pass

def ejecutar(nombre, params=None):
    try:
        consulta = ConsultaSQL.objects.get(nombre=nombre, activa=True)
    except ConsultaSQL.DoesNotExist:
        raise ConsultaNoDisponible(
            f"No existe la consulta activa '{nombre}'. "
            "Ejecuta: python manage.py cargar_consultas"
        )

    with transaction.atomic():
        with connection.cursor() as cursor:
            if connection.vendor == "postgresql":
                cursor.execute("SET TRANSACTION READ ONLY")
            cursor.execute(consulta.sql, params or None)
            columnas = [c[0] for c in cursor.description]
            return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]