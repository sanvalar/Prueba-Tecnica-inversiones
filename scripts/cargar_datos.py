"""
Carga automática de los CSV entregados en PostgreSQL y creación de las vistas SQL.

Uso:
    python scripts/cargar_datos.py                 # crea la base si no existe, crea las tablas,
                                                   # carga los CSV y ejecuta sql/02 ... sql/09
    python scripts/cargar_datos.py --solo-vistas   # solo vuelve a ejecutar sql/02 ... sql/09
                                                   # (no recarga los CSV)

Requiere un archivo .env en la raíz con DB_USER, DB_PASSWORD, DB_HOST, DB_PORT y DB_NAME,
y los CSV entregados en la carpeta data/.
"""
import argparse
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env", override=True)

DATA_DIR = RAIZ / "data"
SQL_DIR = RAIZ / "sql"

# Una tabla por cada CSV entregado, con el mismo nombre del archivo
TABLAS = [
    "cat_perfil_riesgo",
    "catalogo_activos",
    "catalogo_banca",
    "historico_aba_macroactivos",
    "historico_aba_usd_internacional",
]

# Tabla opcional con datos de mercado (archivo generado por scripts/descargar_mercado.py)
TABLA_MERCADO = "mercado_activo"
ARCHIVO_MERCADO = "mercado_resumen.csv"

# Cruce opcional de IDs truncados (lo entrega la fuente original; no se sube a GitHub)
ARCHIVO_MAPA = "mapa_ids_truncados.csv"

VALORES_NULOS = ["", "None", "nan", "NaN", "NA", "N/A", "NULL", None]
VARIABLES_ENV = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]


def verificar_entorno():
    """Falla con un mensaje claro si falta el .env o algún CSV."""
    faltan_env = [v for v in VARIABLES_ENV if not os.getenv(v)]
    if faltan_env:
        sys.exit(f"Faltan variables en el archivo .env: {', '.join(faltan_env)}")


def verificar_csv():
    faltan = [f"{t}.csv" for t in TABLAS if not (DATA_DIR / f"{t}.csv").exists()]
    if faltan:
        sys.exit(
            f"No se encontraron en {DATA_DIR}: {', '.join(faltan)}.\n"
            "Copia allí los CSV entregados (la carpeta data/ no se sube al repositorio)."
        )


def crear_engine(base):
    url = URL.create(
        "postgresql+psycopg2",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=base,
    )
    return create_engine(url)


def crear_base_si_no_existe():
    nombre = os.getenv("DB_NAME")
    admin = create_engine(
        URL.create(
            "postgresql+psycopg2",
            username=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database="postgres",
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


def ejecutar_archivo_sql(engine, ruta):
    sql = ruta.read_text(encoding="utf-8")
    with engine.begin() as con:
        # psycopg2 interpreta '%' como marcador de parámetros; se duplica para que
        # los LIKE '%...%' y los textos con '%' lleguen intactos a PostgreSQL.
        con.exec_driver_sql(sql.replace("%", "%%"))
    print(f"  ejecutado: {ruta.name}")


def detectar_separador(ruta):
    """Los CSV pueden venir con coma o con punto y coma (Excel en español)."""
    with open(ruta, encoding="utf-8-sig") as f:
        encabezado = f.readline()
    return ";" if encabezado.count(";") > encabezado.count(",") else ","


def leer_csv(ruta):
    return pd.read_csv(
        ruta,
        sep=detectar_separador(ruta),
        dtype=str,                 # todo como texto: la limpieza se hace en SQL
        keep_default_na=False,
        na_values=VALORES_NULOS,
        encoding="utf-8-sig",
    )


def cargar_tabla(engine, nombre, ruta=None):
    ruta = ruta or (DATA_DIR / f"{nombre}.csv")
    df = leer_csv(ruta)
    df.columns = [c.strip() for c in df.columns]

    with engine.begin() as con:
        con.execute(text(f'TRUNCATE TABLE "{nombre}"'))
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
    print(f"  {nombre}: {len(df):>6} filas cargadas correctamente.")


def cargar_mercado(engine):
    """Carga los datos de mercado si el archivo existe; si no, el modelo usa riesgos por defecto."""
    ruta = DATA_DIR / ARCHIVO_MERCADO
    if ruta.exists():
        cargar_tabla(engine, TABLA_MERCADO, ruta)
    else:
        print(f"  (sin {ARCHIVO_MERCADO}: el riesgo de las acciones usará el valor por defecto; "
              "genéralo con scripts/descargar_mercado.py)")


def cargar_mapa_ids(engine):
    """Cruce opcional token truncado -> ID real (data/mapa_ids_truncados.csv, columnas token,id_real).

    Solo se usan esas dos columnas; el archivo puede ser el de pendientes ya diligenciado.
    Si no existe, los clientes con ID truncado siguen marcados como tales.
    """
    ruta = DATA_DIR / ARCHIVO_MAPA
    if not ruta.exists():
        with engine.begin() as con:
            con.execute(text("TRUNCATE TABLE mapa_id_truncado"))
        print(f"  (sin {ARCHIVO_MAPA}: los IDs truncados quedan marcados; "
              "ver scripts/exportar_ids_truncados.py)")
        return
    df = leer_csv(ruta)
    df.columns = [c.strip().lower() for c in df.columns]
    if not {"token", "id_real"} <= set(df.columns):
        raise RuntimeError(f"{ARCHIVO_MAPA} debe tener las columnas token e id_real")
    df = df[["token", "id_real"]].dropna(how="any")
    with engine.begin() as con:
        con.execute(text("TRUNCATE TABLE mapa_id_truncado"))
        df.to_sql("mapa_id_truncado", con, if_exists="append", index=False)
    print(f"  mapa_id_truncado: {len(df):>6} filas cargadas (solo las de 10-11 dígitos se aplican).")


def ejecutar_vistas(engine):
    print("Creando vistas de limpieza, portafolio y modelo...")
    for archivo in sorted(SQL_DIR.glob("0[2-9]_*.sql")):
        ejecutar_archivo_sql(engine, archivo)


def main():
    parser = argparse.ArgumentParser(description="Carga los CSV en PostgreSQL y crea las vistas SQL.")
    parser.add_argument("--solo-vistas", action="store_true",
                        help="Solo ejecuta los archivos sql/02 ... sql/09 (no recarga los CSV).")
    parser.add_argument("--vistas", action="store_true", help=argparse.SUPPRESS)  # compatibilidad
    args = parser.parse_args()

    verificar_entorno()
    crear_base_si_no_existe()
    engine = crear_engine(os.getenv("DB_NAME"))

    if not args.solo_vistas:
        verificar_csv()
        print("Creando tablas...")
        ejecutar_archivo_sql(engine, SQL_DIR / "01_crear_tablas.sql")

        print("Cargando CSV...")
        for nombre in TABLAS:
            cargar_tabla(engine, nombre)
        cargar_mercado(engine)
        cargar_mapa_ids(engine)

    ejecutar_vistas(engine)
    print("Listo.")


if __name__ == "__main__":
    main()