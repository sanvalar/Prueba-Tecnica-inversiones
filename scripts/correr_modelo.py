import os, sys
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "modelo"))
from modelo_clientes import (construir_features, segmentar, nombrar_segmento,
                             alinear_perfil, recomendar)

load_dotenv(RAIZ / ".env", override=True)


def main():
    url = URL.create("postgresql+psycopg2",
                     username=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"),
                     host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
                     database=os.getenv("DB_NAME"))
    engine = create_engine(url)

    df = pd.read_sql("SELECT * FROM v_cliente_features", engine)
    print(f"Clientes leídos: {len(df)}")

    f = construir_features(df)
    f, tabla_k, k = segmentar(f)
    print(tabla_k.to_string(index=False)); print("k elegido:", k)

    nombres = f.groupby("segmento_id").apply(nombrar_segmento)
    f["segmento"] = f["segmento_id"].map(nombres)
    f = alinear_perfil(f)
    f["recomendacion"] = f.apply(recomendar, axis=1)

    cols = ["cliente_id", "segmento", "perfil_riesgo", "perfil_implicito", "estado_perfil",
            "score_cop", "score_usd", "recomendacion"]
    f[cols].to_sql("resultado_modelo_cliente", engine, if_exists="replace", index=False)

    print(f["segmento"].value_counts(), "\n")
    print(pd.crosstab(f["perfil_riesgo"], f["estado_perfil"]))


if __name__ == "__main__":
    main()