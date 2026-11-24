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
    {
        "nombre": "modelo_cliente",
        "titulo": "Resultado del modelo analitico por cliente",
        "descripcion": "Segmento, perfil sugerido, estado frente al perfil declarado y recomendacion. Requiere haber ejecutado scripts/correr_modelo.py.",
        "sql": """
SELECT segmento, perfil_riesgo, perfil_implicito, estado_perfil,
       score_cop, score_usd, recomendacion
FROM resultado_modelo_cliente
WHERE cliente_id = %(cliente)s
""".strip(),
    },
    {
        "nombre": "oportunidades",
        "titulo": "Clientes con su resultado del modelo",
        "descripcion": "Una fila por cliente con segmento, estado frente al perfil, patrimonio y recomendacion. Alimenta la pagina Oportunidades.",
        "sql": """
SELECT r.cliente_id, c.banca, c.id_truncado, r.segmento, r.perfil_riesgo,
       r.perfil_implicito, r.estado_perfil, r.score_cop, r.score_usd,
       c.total_cop, c.tiene_portafolio_usd, r.recomendacion
FROM resultado_modelo_cliente r
JOIN v_cliente_resumen c ON c.cliente_id = r.cliente_id
ORDER BY c.total_cop DESC NULLS LAST, r.cliente_id
""".strip(),
    },
    {
        "nombre": "reporte_calidad",
        "titulo": "Reporte de calidad de los datos",
        "descripcion": "Filas crudas, rechazadas, duplicadas y limpias por tabla. Alimenta la pagina Calidad de datos.",
        "sql": """
SELECT tabla, filas_crudas, filas_rechazadas, duplicadas_removidas, filas_limpias
FROM v_reporte_calidad
""".strip(),
    },
    {
        "nombre": "ids_truncados",
        "titulo": "Clientes con identificador truncado",
        "descripcion": "Cuantos clientes tienen el ID en notacion cientifica de Excel.",
        "sql": """
SELECT COUNT(*) FILTER (WHERE id_truncado) AS truncados, COUNT(*) AS clientes
FROM v_cliente_resumen
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