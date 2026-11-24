from django.shortcuts import render
from plotly.offline import get_plotlyjs_version

from . import graficos
from .servicios import ConsultaNoDisponible, ejecutar

# estado del modelo -> (texto corto, color de Bootstrap)
ESTADOS = {
    "ALINEADO": ("Alineado", "success"),
    "MÁS CONSERVADOR QUE SU PERFIL": ("Más conservador que su perfil", "warning"),
    "MÁS RIESGOSO QUE SU PERFIL": ("Más riesgoso que su perfil", "danger"),
    "PERFIL SIN DEFINIR": ("Perfil sin definir", "secondary"),
}
# texto corto para tablas
ESTADOS_CORTO = {
    "ALINEADO": "Alineado",
    "MÁS CONSERVADOR QUE SU PERFIL": "Más conservador",
    "MÁS RIESGOSO QUE SU PERFIL": "Más riesgoso",
    "PERFIL SIN DEFINIR": "Sin perfil",
}


def _plotly_url():
    return f"https://cdn.plot.ly/plotly-{get_plotlyjs_version()}.min.js"


def etiqueta_cliente(cliente_id, truncado=False):
    """Texto legible del cliente. Un ID truncado por Excel se muestra por sus dígitos conocidos."""
    cid = str(cliente_id)
    if not truncado and not cid.startswith("TRUNC-"):
        return cid
    digitos = cid.replace("TRUNC-", "")
    base, _, perfil = digitos.partition("#")
    texto = f"ID truncado {base}…"
    return f"{texto} (perfil {perfil})" if perfil else texto


def _posicion(score):
    """Posición (0-100 %) de un puntaje 1-5 sobre la escala de riesgo."""
    if score is None:
        return None
    return round(min(max((float(score) - 1) / 4 * 100, 0), 100), 1)


def _enriquecer_estado(fila):
    texto, clase = ESTADOS.get(fila.get("estado_perfil"), (fila.get("estado_perfil"), "secondary"))
    fila["estado_texto"], fila["estado_clase"] = texto, clase
    fila["estado_corto"] = ESTADOS_CORTO.get(fila.get("estado_perfil"), texto)
    return fila


def portafolio(request):
    contexto = {"plotly_url": _plotly_url()}
    try:
        clientes = ejecutar("clientes")
        for c in clientes:
            c["etiqueta"] = etiqueta_cliente(c["cliente_id"], c["id_truncado"])
        cliente_id = request.GET.get("cliente", "").strip()
        # Solo se acepta un cliente que exista en la lista (evita valores arbitrarios)
        actual = next((c for c in clientes if c["cliente_id"] == cliente_id), None)
        contexto.update(clientes=clientes, cliente_sel=cliente_id, actual=actual)

        if actual:
            params = {"cliente": cliente_id}

            local_detalle = ejecutar("local_detalle", params)
            local_macro = ejecutar("local_por_macroactivo", params)
            contexto["local_detalle"] = local_detalle
            contexto["grafico_cop_dona"] = graficos.dona(
                local_macro, "macroactivo", "valor_cop", "Composición por macroactivo")
            contexto["grafico_cop_barras"] = graficos.barras(
                local_detalle, "activo", "valor_cop", "Mayores posiciones")

            if actual["tiene_portafolio_usd"]:
                usd_detalle = ejecutar("usd_detalle", params)
                usd_tipo = ejecutar("usd_por_tipo", params)
                contexto["usd_detalle"] = usd_detalle
                contexto["grafico_usd_dona"] = graficos.dona(
                    usd_tipo, "tipo_activo", "valor_usd", "Composición por tipo de activo")
                contexto["grafico_usd_barras"] = graficos.barras(
                    usd_detalle, "nombre_activo", "valor_usd", "Mayores posiciones")

            # Resultado del modelo analítico. Va aparte: si la tabla resultado_modelo_cliente
            # no existe (no se ha corrido scripts/correr_modelo.py) o la consulta falla, el
            # resto de la página sigue funcionando y la plantilla muestra un aviso.
            try:
                filas = ejecutar("modelo_cliente", params)
            except Exception:
                filas = []
            if filas:
                m = _enriquecer_estado(filas[0])
                m["pos_cop"] = _posicion(m.get("score_cop"))
                m["pos_usd"] = _posicion(m.get("score_usd"))
                m["recomendaciones"] = (m.get("recomendacion") or "").splitlines()
                contexto["modelo"] = m
    except ConsultaNoDisponible as error:
        contexto["error"] = str(error)

    return render(request, "portafolios/portafolio.html", contexto)


def oportunidades(request):
    contexto = {"plotly_url": _plotly_url()}
    try:
        filas = ejecutar("oportunidades")
    except ConsultaNoDisponible as error:
        contexto["error"] = str(error)
        return render(request, "portafolios/oportunidades.html", contexto)
    except Exception:
        contexto["error"] = ("Todavía no hay resultados del modelo. "
                             "Ejecuta: python scripts/correr_modelo.py")
        return render(request, "portafolios/oportunidades.html", contexto)

    for f in filas:
        _enriquecer_estado(f)
        f["etiqueta"] = etiqueta_cliente(f["cliente_id"], f["id_truncado"])
        f["primera_recomendacion"] = (f.get("recomendacion") or "").splitlines()[0:1]

    conteo = {}
    for f in filas:
        conteo[f["estado_perfil"]] = conteo.get(f["estado_perfil"], 0) + 1
    resumen = [
        {"clave": k, "texto": ESTADOS[k][0], "clase": ESTADOS[k][1], "n": conteo.get(k, 0)}
        for k in ESTADOS
    ]

    estado = request.GET.get("estado", "").strip()
    visibles = [f for f in filas if not estado or f["estado_perfil"] == estado]

    por_segmento = {}
    for f in filas:
        por_segmento[f["segmento"]] = por_segmento.get(f["segmento"], 0) + 1

    contexto.update(
        total=len(filas),
        resumen=resumen,
        estado_sel=estado,
        filas=visibles,
        grafico_estados=graficos.dona_simple(
            [r["texto"] for r in resumen], [r["n"] for r in resumen],
            "Clientes según su perfil", colores=["#2e8b57", "#e0a100", "#c0392b", "#8a94a0"]),
        grafico_segmentos=graficos.barras_simple(
            list(por_segmento.keys()), list(por_segmento.values()), "Clientes por segmento"),
    )
    return render(request, "portafolios/oportunidades.html", contexto)


def calidad(request):
    contexto = {}
    try:
        contexto["reporte"] = ejecutar("reporte_calidad")
        contexto["truncados"] = ejecutar("ids_truncados")[0]
    except ConsultaNoDisponible as error:
        contexto["error"] = str(error)
    except Exception:
        contexto["error"] = "No se pudo leer el reporte de calidad. ¿Se ejecutó scripts/cargar_datos.py?"
    return render(request, "portafolios/calidad.html", contexto)
