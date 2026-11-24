import plotly.graph_objects as go

PALETA = ["#0b3b66", "#2a7ab0", "#f0b429", "#4c9f70", "#c0504d", "#8e7cc3", "#8a94a0"]
FUENTE = dict(family="system-ui, -apple-system, Segoe UI, Roboto, sans-serif", size=13, color="#1f2937")


def _a_html(fig, titulo, alto=340):
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=15), x=0.0, xanchor="left"),
        height=alto,
        margin=dict(t=50, b=20, l=10, r=10),
        font=FUENTE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.1),
        colorway=PALETA,
    )
    return fig.to_html(full_html=False, include_plotlyjs=False,
                       config={"displayModeBar": False, "responsive": True})


def dona_simple(etiquetas, valores, titulo, colores=None):
    if not valores or sum(valores) <= 0:
        return None
    fig = go.Figure(go.Pie(
        labels=etiquetas, values=valores, hole=0.58, sort=False, textinfo="value",
        marker=dict(colors=colores or PALETA, line=dict(color="#ffffff", width=2)),
    ))
    return _a_html(fig, titulo)


def dona(filas, etiqueta, valor, titulo):
    """Dona de composición. Solo incluye valores positivos (una torta no admite negativos)."""
    datos = [(f[etiqueta], float(f[valor])) for f in filas if f[valor] is not None and f[valor] > 0]
    if not datos:
        return None
    fig = go.Figure(go.Pie(
        labels=[d[0] for d in datos], values=[d[1] for d in datos],
        hole=0.58, sort=False, textinfo="percent",
        marker=dict(line=dict(color="#ffffff", width=2)),
    ))
    return _a_html(fig, titulo)


def barras(filas, etiqueta, valor, titulo, n=8, max_caracteres=34):
    """Barras horizontales con las n posiciones más grandes (las filas ya vienen ordenadas)."""
    datos = [(str(f[etiqueta]).strip()[:max_caracteres], float(f[valor]))
             for f in filas if f[valor] is not None][:n]
    if not datos:
        return None
    datos.reverse()  # para que la mayor quede arriba
    fig = go.Figure(go.Bar(
        x=[d[1] for d in datos], y=[d[0] for d in datos], orientation="h",
        marker=dict(color=PALETA[0]),
        hovertemplate="%{y}<br>%{x:,.0f}<extra></extra>",
    ))
    fig.update_xaxes(showgrid=True, gridcolor="#e5e7eb", zeroline=False, tickformat="~s")
    fig.update_yaxes(automargin=True)
    fig.update_layout(bargap=0.45)
    return _a_html(fig, titulo, alto=max(260, 120 + 38 * len(datos)))


def barras_simple(etiquetas, valores, titulo):
    if not valores:
        return None
    pares = sorted(zip(etiquetas, valores), key=lambda p: p[1])
    fig = go.Figure(go.Bar(
        x=[p[1] for p in pares], y=[p[0] for p in pares], orientation="h",
        marker=dict(color=PALETA[1]), text=[p[1] for p in pares], textposition="outside",
        hovertemplate="%{y}: %{x}<extra></extra>",
    ))
    fig.update_xaxes(showgrid=False, visible=False)
    fig.update_yaxes(automargin=True)
    fig.update_layout(bargap=0.45)
    return _a_html(fig, titulo)
