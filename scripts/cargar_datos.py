import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env", override=True)

DATA_DIR = RAIZ / "data"
SQL_DIR = RAIZ / "sql"


TABLAS = [
    "cat_perfil_riesgo",
    "catalogo_activos",
    "catalogo_banca",
    "historico_aba_macroactivos",
    "historico_aba_usd_internacional"
]


VALORES_NULOS = ["", "None", "nan", "NaN", "NA", "N/A", "NULL", None]

print(RAIZ)
print(DATA_DIR.exists(), SQL_DIR.exists())

def crear_engine(base):
    url = URL.create(
        "postgresql+psycopg2",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=base
    )
    return create_engine(url)

if __name__ == "__main__":
    engine = crear_engine(os.getenv("analitica_inversiones"))
    with engine.connect() as con:
        print(con.execute(text("SELECT version()")).scalar())
        
        
        
# ETAPA 3

def crear_base_si_no_existe():
    nombre = os.getenv("DB_NAME")
    admin = create_engine(
        URL.create(
            "postgresql+psycopg2",
            username=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database="postgres"
        ),
        isolation_level="AUTOCOMMIT",
        
        
    )
    with admin.connect() as con:
        existe = con.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": nombre}
        ).scalar()
        if not existe:
            con.execute(text(f'CREATE DATABASE "{nombre}"'))
            print(f"Base de datos '{nombre}' creada.")
        else:
            print(f"Base de datos '{nombre}' ya existía.")
    admin.dispose()
    
    
if __name__ == "__main__":
    crear_base_si_no_existe()
    
#ETAPA 4
def ejecutar_archivo_sql(engine, ruta):
    with engine.begin() as con:
        con.exec_driver_sql(ruta.read_text(encoding="utf-8"))
    print(f"  ejecutado: {ruta.name}")
    
if __name__ == "__main__":
    crear_base_si_no_existe()
    engine = crear_engine(os.getenv("DB_NAME"))
    ejecutar_archivo_sql(engine, SQL_DIR / "01_crear_tablas.sql")
    
    
#ETAPA 5
def leer_csv(nombre):
    return pd.read_csv(
        DATA_DIR / f"{nombre}.csv",
        dtype=str,
        keep_default_na=False,
        na_values=VALORES_NULOS,
        encoding="utf-8-sig",
    )
    
if __name__ == "__main__":
    df = leer_csv("catalogo_banca")
    print(df)
    print(df.dtypes)
    
    
#ETAPA 6

def cargar_tabla(engine, nombre):
    df = leer_csv(nombre)
    df.columns = [c.strip() for c in df.columns]
    
    
    with engine.begin() as con:
        con.execute(text(f'TRUNCATE TABLE"{nombre}"'))
        df.to_sql(
            nombre,
            con,
            if_exists="append",
            index=False,
            chunksize=2000,
            method="multi",
            
        )
        
        en_bd = con.execute(text(f'SELECT COUNT(*) FROM "{nombre}"')).scalar()
        if en_bd != len(df):
            raise RuntimeError(
                f"{nombre}: el CSV tiene {len(df)} filas pero la tabla quedó con {en_bd}"
            )
            
    print(f" {nombre}: {len(df):>6} filas cargadas correctamente.")
    
    
if __name__ == "__main__":
    crear_base_si_no_existe()
    engine = crear_engine(os.getenv("DB_NAME"))
    ejecutar_archivo_sql(engine, SQL_DIR / "01_crear_tablas.sql")
    cargar_tabla(engine, "catalogo_banca")
    
    
#ETAPA 7
def main():
    crear_base_si_no_existe()
    engine = crear_engine(os.getenv("DB_NAME"))

    print("Creando tablas...")
    ejecutar_archivo_sql(engine, SQL_DIR / "01_crear_tablas.sql")

    print("Cargando CSV...")
    for nombre in TABLAS:
        cargar_tabla(engine, nombre)

    print("Creando vistas de limpieza y portafolio...")
    for archivo in sorted(SQL_DIR.glob("0[2-9]_*.sql")):
        ejecutar_archivo_sql(engine, archivo)
    print("Listo.")


if __name__ == "__main__":
    main()