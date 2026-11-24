"""Exporta los IDs truncados por Excel que siguen pendientes, para pedir el ID real a la fuente.

Uso:
    python scripts/exportar_ids_truncados.py

Genera data/ids_truncados_pendientes.csv (token, id_real vacío, y contexto para identificar
al cliente en el sistema origen: perfil, banca, última fecha, valor). Quien tenga la base
original diligencia la columna id_real (10-11 dígitos) y guarda el archivo como
data/mapa_ids_truncados.csv. Luego:

    python scripts/cargar_datos.py     # aplica el cruce y rehace las vistas
    python scripts/correr_modelo.py    # recalcula el modelo

El archivo contiene datos de clientes: está en .gitignore y NO se sube a GitHub.
"""
import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env", override=True)

CONSULTA = """
SELECT cliente_id AS token,
       ''::text   AS id_real,
       perfil_riesgo, banca,
       fecha_cop  AS ultima_fecha,
       ROUND(total_cop) AS total_cop,
       n_posiciones_cop AS posiciones
FROM v_cliente_resumen
WHERE id_truncado
ORDER BY cliente_id
"""


def main():
    url = URL.create("postgresql+psycopg2",
                     username=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"),
                     host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
                     database=os.getenv("DB_NAME"))
    df = pd.read_sql(CONSULTA, create_engine(url))
    salida = RAIZ / "data" / "ids_truncados_pendientes.csv"
    salida.parent.mkdir(exist_ok=True)
    df.to_csv(salida, index=False, encoding="utf-8-sig")
    print(f"{len(df)} clientes con ID truncado pendiente -> {salida}")
    print("Diligencia id_real y guarda como data/mapa_ids_truncados.csv")


if __name__ == "__main__":
    main()
