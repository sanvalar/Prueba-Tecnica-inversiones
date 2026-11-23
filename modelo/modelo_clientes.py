"""Modelo analítico por clientes y alineación de perfil/riesgo + recomendaciones """
import numpy as np 
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

#---Supuestos de negocio

RIESGO_COP = {"rf": 1.5, "fic":2.5, "rv":4.5}
RIESGO_USD = {"liq": 1.0, "rf": 1.5, "fondos": 2.5, "acc": 4.0}
BANDAS = [("CONSERVADOR", 0, 2.75), ("MODERADO", 2.75, 3.75), ("AGRESIVO", 3.75, 5.01)]
ORDEN = {"CONSERVADOR": 1, "MODERADO": 2, "AGRESIVO": 3}
FEATURES_CLUSTER = ["log_total_cop", "pct_rv", "pct_fic", "pct_rf",
                    "score_cop", "concentracion", "n_posiciones_cop"]


def perfil_por_score(score):
    for nombre, lo, hi in BANDAS:
        if lo <= score < hi:
            return nombre
    return None


def construir_features(df: pd.DataFrame) -> pd.DataFrame:
    """df = vista v_cliente_features (una fila por cliente)."""
    f = df.copy()
    num = ["total_cop", "cop_renta_fija", "cop_renta_variable", "cop_fics",
           "concentracion_max_cop", "n_posiciones_cop", "total_usd",
           "usd_liquidez", "usd_renta_fija", "usd_fondos", "usd_acciones_etfs"]
    for c in num:
        f[c] = pd.to_numeric(f[c], errors="coerce").fillna(0.0)

    tot = f["total_cop"].where(f["total_cop"] > 0)
    f["pct_rf"] = (f["cop_renta_fija"] / tot).fillna(0)
    f["pct_rv"] = (f["cop_renta_variable"] / tot).fillna(0)
    f["pct_fic"] = (f["cop_fics"] / tot).fillna(0)
    f["score_cop"] = (f["pct_rf"] * RIESGO_COP["rf"]
                      + f["pct_fic"] * RIESGO_COP["fic"]
                      + f["pct_rv"] * RIESGO_COP["rv"])
    f["log_total_cop"] = np.log10(f["total_cop"].clip(lower=1))
    c = f["concentracion_max_cop"]
    f["concentracion"] = np.where(c > 1.0, c / 100.0, c)

    # riesgo USD: solo saldos positivos (los deudores de liquidez distorsionarían)
    pos = {k: f[col].clip(lower=0) for k, col in
           [("liq", "usd_liquidez"), ("rf", "usd_renta_fija"),
            ("fondos", "usd_fondos"), ("acc", "usd_acciones_etfs")]}
    base = sum(pos.values())
    f["score_usd"] = np.where(
        base > 0,
        sum(pos[k] * RIESGO_USD[k] for k in pos) / base.replace(0, np.nan),
        np.nan)
    return f


def segmentar(f: pd.DataFrame, k_min=2, k_max=5, min_tam=2, semilla=42):
    """K-Means con k elegido por silueta; descarta k que dejan un grupo de < min_tam clientes."""
    X = StandardScaler().fit_transform(f[FEATURES_CLUSTER])
    resultados = []
    for k in range(k_min, min(k_max, len(f) - 1) + 1):
        km = KMeans(n_clusters=k, n_init=20, random_state=semilla).fit(X)
        tam = np.bincount(km.labels_)
        sil = silhouette_score(X, km.labels_)
        resultados.append((k, sil, tam.min() >= min_tam, km.labels_))
    validos = [r for r in resultados if r[2]] or resultados
    k, sil, _, etiquetas = max(validos, key=lambda r: r[1])
    out = f.copy()
    out["segmento_id"] = etiquetas
    tabla = pd.DataFrame([(r[0], round(r[1], 3), r[2]) for r in resultados],
                         columns=["k", "silueta", "tamano_ok"])
    return out, tabla, k


def nombrar_segmento(g: pd.DataFrame) -> str:
    rv, fic, rf = g["pct_rv"].mean(), g["pct_fic"].mean(), g["pct_rf"].mean()
    m = g["log_total_cop"].mean()
    tam = "patrimonio alto" if m >= 8 else ("patrimonio medio" if m >= 6.5 else "patrimonio bajo")
    if max(rv, fic, rf) < 0.6:
        base = "Diversificado"
    else:
        base = {"rv": "Renta variable", "fic": "FICs", "rf": "Renta fija"}[
            max([("rv", rv), ("fic", fic), ("rf", rf)], key=lambda t: t[1])[0]]
    return f"{base} · {tam}"


def alinear_perfil(f: pd.DataFrame) -> pd.DataFrame:
    out = f.copy()
    out["perfil_implicito"] = out["score_cop"].apply(perfil_por_score)

    def estado(r):
        if r["perfil_riesgo"] in (None, "SIN DEFINIR") or pd.isna(r["perfil_riesgo"]):
            return "PERFIL SIN DEFINIR"
        d = ORDEN[r["perfil_implicito"]] - ORDEN[r["perfil_riesgo"]]
        if d == 0:
            return "ALINEADO"
        return "MÁS RIESGOSO QUE SU PERFIL" if d > 0 else "MÁS CONSERVADOR QUE SU PERFIL"

    out["estado_perfil"] = out.apply(estado, axis=1)
    return out


def recomendar(r) -> str:
    msgs = []
    if r["estado_perfil"] == "PERFIL SIN DEFINIR":
        msgs.append(f"Completar el perfil de riesgo (su portafolio se comporta como {r['perfil_implicito'].lower()}).")
    elif r["estado_perfil"].startswith("MÁS RIESGOSO"):
        msgs.append(f"Revisar exposición: su portafolio es {r['perfil_implicito'].lower()} y su perfil es {r['perfil_riesgo'].lower()}; valorar mover parte a renta fija/FICs.")
    elif r["estado_perfil"].startswith("MÁS CONSERVADOR"):
        msgs.append(f"Oportunidad: su perfil es {r['perfil_riesgo'].lower()} y el portafolio es {r['perfil_implicito'].lower()}; hay espacio para más riesgo.")
    if r["concentracion"] >= 0.8 and r["n_posiciones_cop"] <= 2:
        msgs.append("Alta concentración (≥80% en una posición): diversificar entre emisores.")
    if not bool(r["tiene_portafolio_usd"]) and r["total_cop"] >= 5e7:
        msgs.append("Patrimonio local relevante sin portafolio internacional: evaluar diversificación en USD.")
    if r["pct_rv"] >= 0.9 and r["total_cop"] < 5e6:
        msgs.append("Portafolio pequeño 100% en acciones: considerar fondos para diversificar con montos bajos.")
    return " ".join(msgs) if msgs else "Sin alertas: portafolio coherente con su perfil."
