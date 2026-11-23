from django.core.management.base import BaseCommand

from portafolios.models import ConsultaSQL

CONSULTAS = [
    {
        "nombre": "clientes",
        "titulo": "Lista de clientes con su resumen",
        "descripcion": "Una fila por cliente. Alimenta el selector de la pantalla principal.",
        "sql": """
SELECT cliente_id, banca, perfil_riesgo, id_truncado, tiene_portafolio_usd,
       fecha_cop, total_cop, n_posiciones_cop,
       fecha_usd, total_usd, n_posiciones_usd
FROM v_cliente_resumen
ORDER BY total_cop DESC NULLS LAST, cliente_id
""".strip(),
    },
    {
        "nombre": "local_por_macroactivo",
        "titulo": "Portafolio local (COP) por macroactivo",
        "descripcion": "Total en COP por macroactivo, a la ultima fecha del cliente.",
        "sql": """
SELECT macroactivo, SUM(valor_cop) AS valor_cop
FROM v_portafolio_local_ultimo
WHERE cliente_id = %(cliente)s
GROUP BY macroactivo
ORDER BY valor_cop DESC
""".strip(),
    },
    {
        "nombre": "local_detalle",
        "titulo": "Portafolio local (COP) en detalle",
        "descripcion": "Posiciones del cliente en COP a su ultima fecha.",
        "sql": """
SELECT macroactivo, activo, valor_cop, participacion_pct, fecha
FROM v_portafolio_local_ultimo
WHERE cliente_id = %(cliente)s
ORDER BY valor_cop DESC
""".strip(),
    },
    {
        "nombre": "usd_por_tipo",
        "titulo": "Portafolio internacional (USD) por tipo de activo",
        "descripcion": "Total en USD por tipo de activo, a la ultima fecha del cliente.",
        "sql": """
SELECT tipo_activo, SUM(valor_usd) AS valor_usd
FROM v_portafolio_usd_ultimo
WHERE cliente_id = %(cliente)s
GROUP BY tipo_activo
ORDER BY valor_usd DESC
""".strip(),
    },
    {
        "nombre": "usd_detalle",
        "titulo": "Portafolio internacional (USD) en detalle",
        "descripcion": "Posiciones del cliente en USD a su ultima fecha.",
        "sql": """
SELECT tipo_activo, nombre_activo, cantidad, valor_usd, participacion_pct,
       fecha, fecha_vencimiento, tasa_cupon
FROM v_portafolio_usd_ultimo
WHERE cliente_id = %(cliente)s
ORDER BY valor_usd DESC
""".strip(),
    },
]


class Command(BaseCommand):
    help = "Carga las consultas SQL base. No pisa las que ya existen ni sus cambios hechos en el admin."

    def handle(self, *args, **options):
        for datos in CONSULTAS:
            if ConsultaSQL.objects.filter(nombre=datos["nombre"]).exists():
                self.stdout.write(f"  ya existe: {datos['nombre']}")
                continue
            consulta = ConsultaSQL(**datos)
            consulta.full_clean()      # aplica la misma validacion que el admin
            consulta.save()
            self.stdout.write(self.style.SUCCESS(f"  creada: {datos['nombre']}"))