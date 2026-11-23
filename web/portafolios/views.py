from django.shortcuts import render
from plotly.offline import get_plotlyjs_version

from . import graficos
from .servicios import ConsultaNoDisponible, ejecutar


def portafolio(request):
    contexto = {
        "plotly_url": f"https://cdn.plot.ly/plotly-{get_plotlyjs_version()}.min.js",
    }
    try:
        clientes = ejecutar("clientes")
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
                local_macro, "macroactivo", "valor_cop", "Composición por macroactivo (COP)")
            contexto["grafico_cop_barras"] = graficos.barras(
                local_detalle, "activo", "valor_cop", "Mayores posiciones (COP)")

            if actual["tiene_portafolio_usd"]:
                usd_detalle = ejecutar("usd_detalle", params)
                usd_tipo = ejecutar("usd_por_tipo", params)
                contexto["usd_detalle"] = usd_detalle
                contexto["grafico_usd_dona"] = graficos.dona(
                    usd_tipo, "tipo_activo", "valor_usd", "Composición por tipo de activo (USD)")
                contexto["grafico_usd_barras"] = graficos.barras(
                    usd_detalle, "nombre_activo", "valor_usd", "Mayores posiciones (USD)")
    except ConsultaNoDisponible as error:
        contexto["error"] = str(error)

    return render(request, "portafolios/portafolio.html", contexto)