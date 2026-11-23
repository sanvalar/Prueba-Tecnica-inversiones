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
    