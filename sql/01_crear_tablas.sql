CREATE TABLE IF NOT EXISTS cat_perfil_riesgo (
    cod_perfil_riesgo TEXT,
    perfil_riesgo TEXT
);

CREATE TABLE IF NOT EXISTS catalogo_activos (
    activo TEXT,
    cod_activo TEXT
);

CREATE TABLE IF NOT EXISTS catalogo_banca (
    cod_banca TEXT,
    banca TEXT
);

CREATE TABLE IF NOT EXISTS historico_aba_macroactivos (
    ingestion_year TEXT,
    ingestion_month TEXT,
    ingestion_day TEXT,
    id_sistema_cliente TEXT,
    macroactivo TEXT,
    cod_activo TEXT,
    aba TEXT, 
    cod_perfil_riesgo TEXT,
    cod_banca TEXT,
    year TEXT,
    month TEXT
);

CREATE TABLE IF NOT EXISTS historico_aba_usd_internacional (
    ingestion_year TEXT,
    ingestion_month TEXT,
    ingestion_day TEXT,
    id_sistema_cliente TEXT,
    simbol TEXT, 
    cusip TEXT,
    isin TEXT,
    nombre_activo TEXT,
    cantidad TEXT,
    valor_mercado TEXT,
    fecha_vencimiento TEXT,
    tasa_cupon TEXT
);

-- Datos de mercado por activo (scripts/descargar_mercado.py). Opcional: puede quedar vacía.
CREATE TABLE IF NOT EXISTS mercado_activo (
    activo            TEXT,
    ticker            TEXT,
    mercado           TEXT,
    dias              TEXT,
    desde             TEXT,
    hasta             TEXT,
    retorno_1a        TEXT,
    volatilidad_anual TEXT,
    max_drawdown      TEXT
);

-- Cruce opcional de IDs truncados por Excel -> ID real (lo entrega la fuente original).
-- Se llena con data/mapa_ids_truncados.csv (columnas token,id_real). Puede quedar vacía.
CREATE TABLE IF NOT EXISTS mapa_id_truncado (
    token   TEXT,
    id_real TEXT
);
