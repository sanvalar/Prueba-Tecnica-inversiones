"""
Descarga datos de mercado (último año) con yfinance y calcula, por activo:
retorno a 1 año, volatilidad anualizada y máxima caída (max drawdown).
Resultado: data/mercado_resumen.csv  (data/ está en .gitignore)

Uso:  python scripts/descargar_mercado.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "data" / "mercado_resumen.csv"

# ---------------------------------------------------------------------------
# 1) Listas de activos a consultar
# Local (COP): nombre en tu base -> ticker en Yahoo Finance (terminan en .CL).
# Verifica cada ticker buscándolo en https://finance.yahoo.com antes de confiar.
LOCAL = {
    "ECOPETROL": "ECOPETROL.CL",
    "ISA": "ISA.CL",
    "PFGRUPSURA": "PFGRUPSURA.CL",
    "CELSIA": "CELSIA.CL",
    "GRUBOLIVAR": "GRUBOLIVAR.CL",
    "CEMARGOS": "CEMARGOS.CL",
    "PFCORFICOL": "PFCORFICOL.CL",
    "PFBCOLOM": "PFCIBEST.CL",  # Bancolombia pasó a llamarse Cibest en 2025 (PFBCOLOM -> PFCIBEST)
    "ETB": "ETB.CL",
}
# Internacional (USD): símbolos de acciones/ETFs que aparecen en tu CSV de USD.
USD = ["AAPL", "AMZN", "GOOG", "META", "NFLX", "DIS", "BRK-B", "AMD", "SOFI", "C",
       "PBR", "PLTR", "PYPL", "LYG", "XLB", "XLF", "EEM", "VGK", "SOXL"]
# ---------------------------------------------------------------------------


def resumen(nombre, ticker, mercado):
    """Devuelve un dict con las métricas de un activo, o None si falla."""
    try:
        # Ticker().history devuelve columnas simples (Open, High, Low, Close...)
        h = yf.Ticker(ticker).history(period="1y", auto_adjust=True)
    except Exception as e:  # sin internet, ticker raro, etc.
        print(f"ERROR {ticker}: {e}")
        return None

    if h.empty or "Close" not in h:
        print(f"SIN DATOS: {ticker}")
        return None

    precios = h["Close"].dropna()
    if len(precios) < 30:
        print(f"POCOS DATOS ({len(precios)} días): {ticker}")
        return None

    rend_diario = precios.pct_change().dropna()
    return {
        "activo": nombre,
        "ticker": ticker,
        "mercado": mercado,
        "dias": len(precios),
        "desde": precios.index[0].date().isoformat(),
        "hasta": precios.index[-1].date().isoformat(),
        "retorno_1a": float(precios.iloc[-1] / precios.iloc[0] - 1),
        "volatilidad_anual": float(rend_diario.std() * np.sqrt(252)),
        "max_drawdown": float((precios / precios.cummax() - 1).min()),
    }


def main():
    filas = [resumen(n, t, "COP") for n, t in LOCAL.items()]
    filas += [resumen(t, t, "USD") for t in USD]
    filas = [f for f in filas if f]

    if not filas:
        print("No se descargó nada. Revisa tu conexión a internet y los tickers.")
        return

    df = pd.DataFrame(filas)
    SALIDA.parent.mkdir(exist_ok=True)
    df.to_csv(SALIDA, index=False)

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", None)
    print(df.round(3).to_string(index=False))
    print(f"\nGuardado en: {SALIDA}")


if __name__ == "__main__":
    main()