import plotly.graph_objects as go


def _a_html(fig, titulo):
    fig.update_layout(
        title=titulo,
        height=380,
        margin=dict(t=50, b=20, l=20, r=20),
        legend=dict(orientation="h"),
    )
    return fig.to_html(full_html=False, include_plotlyjs=False, config={"displayModeBar": False})


def dona(filas, etiqueta, valor, titulo):
    """Dona de composicion. Solo incluye valores positivos (una torta no admite negativos)."""
    datos = [(f[etiqueta], float(f[valor])) for f in filas if f[valor] is not None and f[valor] > 0]
    if not datos:
        return None
    fig = go.Figure(go.Pie(
        labels=[d[0] for d in datos],
        values=[d[1] for d in datos],
        hole=0.45, sort=False, textinfo="percent",
    ))
    return _a_html(fig, titulo)


def barras(filas, etiqueta, valor, titulo, n=10, max_caracteres=38):
    """Barras horizontales con las n posiciones mas grandes (las filas ya vienen ordenadas)."""
    datos = [(str(f[etiqueta])[:max_caracteres], float(f[valor])) for f in filas if f[valor] is not None][:n]
    if not datos:
        return None
    datos.reverse()                      # para que la mayor quede arriba
    fig = go.Figure(go.Bar(
        x=[d[1] for d in datos],
        y=[d[0] for d in datos],
        orientation="h",
    ))
    return _a_html(fig, titulo)