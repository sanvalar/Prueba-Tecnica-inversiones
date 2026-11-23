--VISTAS
--Etapa 1
DROP VIEW IF EXISTS v_cliente_resumen CASCADE;
DROP VIEW IF EXISTS v_portafolio_usd_ultimo CASCADE;
DROP VIEW IF EXISTS v_portafolio_local_ultimo CASCADE;
DROP VIEW IF EXISTS v_reporte_calidad CASCADE;
DROP VIEW IF EXISTS v_usd_limpio CASCADE;
DROP VIEW IF EXISTS v_usd_rechazados CASCADE;
DROP VIEW IF EXISTS v_usd_parseado CASCADE;
DROP VIEW IF EXISTS v_macro_limpio CASCADE;
DROP VIEW IF EXISTS v_macro_rechazados CASCADE;
DROP VIEW IF EXISTS v_macro_parseado CASCADE;
DROP VIEW IF EXISTS v_cat_activos CASCADE;
DROP VIEW IF EXISTS v_cat_banca CASCADE;
DROP VIEW IF EXISTS v_cat_perfil_riesgo CASCADE;


CREATE OR REPLACE VIEW v_cat_perfil_riesgo AS
SELECT DISTINCT
    TRIM(cod_perfil_riesgo)    AS cod_perfil_riesgo,
    UPPER(TRIM(perfil_riesgo)) AS perfil_riesgo
FROM cat_perfil_riesgo;

CREATE OR REPLACE VIEW v_cat_banca AS
SELECT DISTINCT
    TRIM(cod_banca) AS cod_banca,
    TRIM(banca)     AS banca
FROM catalogo_banca;

CREATE OR REPLACE VIEW v_cat_activos AS
SELECT DISTINCT
    CASE WHEN TRIM(cod_activo) = '1115' THEN '1015' ELSE TRIM(cod_activo) END AS cod_activo,
    TRIM(activo)                                                              AS activo,
    (TRIM(cod_activo) = '1115')                                               AS codigo_corregido
FROM catalogo_activos;


---Etapa 2
CREATE OR REPLACE VIEW v_macro_parseado AS
WITH p AS (
    SELECT
        m.*,
        COALESCE(ingestion_month, month) AS mes_txt,
        CASE WHEN ingestion_year ~ '^20[0-9]{2}$'
              AND COALESCE(ingestion_month, month) ~ '^(0?[1-9]|1[0-2])$'
              AND ingestion_day ~ '^(0?[1-9]|[12][0-9]|3[01])$'
             THEN make_date(ingestion_year::int, COALESCE(ingestion_month, month)::int, 1)
                  + (ingestion_day::int - 1)
        END AS fecha_calc,
        CASE WHEN aba ~ '^[0-9]+(\.[0-9]+)?$' THEN aba::numeric END AS aba_cop
    FROM historico_aba_macroactivos m
),
q AS (
    SELECT
        p.*,
        CASE WHEN fecha_calc IS NULL THEN NULL
             WHEN EXTRACT(MONTH FROM fecha_calc) = mes_txt::int THEN fecha_calc
        END AS fecha
    FROM p
)
SELECT
    q.*,
    COALESCE(
        fecha IS NOT NULL
        AND aba_cop IS NOT NULL
        AND id_sistema_cliente ~ '^([0-9]{10,}|[0-9]\.[0-9]+E\+[0-9]+)$'
        AND (macroactivo IS NULL OR macroactivo IN ('Renta Variable', 'FICs', 'Renta Fija'))
        AND (cod_banca IS NULL OR cod_banca IN (SELECT cod_banca FROM v_cat_banca))
        AND (cod_perfil_riesgo IS NULL
             OR cod_perfil_riesgo IN (SELECT cod_perfil_riesgo FROM v_cat_perfil_riesgo))
        AND (cod_activo IS NULL OR cod_activo ~ '^[0-9]{4,5}$'),
        false
    ) AS es_valida
FROM q;


---Etapa 3

CREATE OR REPLACE VIEW v_macro_rechazados AS
SELECT ingestion_year, ingestion_month, ingestion_day, id_sistema_cliente,
       macroactivo, cod_activo, aba, cod_perfil_riesgo, cod_banca, year, month
FROM v_macro_parseado
WHERE NOT es_valida;


---Etapa 4
CREATE OR REPLACE VIEW v_macro_limpio AS
WITH validas AS (
    SELECT
        fecha,
        id_sistema_cliente                         AS cliente_id,
        (POSITION('E+' IN id_sistema_cliente) > 0) AS id_truncado,
        cod_activo,
        aba_cop,
        MAX(macroactivo)       AS macroactivo,
        MAX(cod_perfil_riesgo) AS cod_perfil_riesgo,
        MAX(cod_banca)         AS cod_banca
    FROM v_macro_parseado
    WHERE es_valida
    GROUP BY fecha, id_sistema_cliente, cod_activo, aba_cop
),
mapa_macro AS (
    SELECT DISTINCT ON (cod_activo) cod_activo, macroactivo
    FROM (
        SELECT cod_activo, macroactivo, COUNT(*) AS n
        FROM validas
        WHERE cod_activo IS NOT NULL AND macroactivo IS NOT NULL
        GROUP BY cod_activo, macroactivo
    ) t
    ORDER BY cod_activo, n DESC
),
dim_perfil AS (
    SELECT DISTINCT ON (cliente_id) cliente_id, cod_perfil_riesgo
    FROM validas
    WHERE cod_perfil_riesgo IS NOT NULL
    ORDER BY cliente_id, fecha DESC
),
dim_banca AS (
    SELECT DISTINCT ON (cliente_id) cliente_id, cod_banca
    FROM validas
    WHERE cod_banca IS NOT NULL
    ORDER BY cliente_id, fecha DESC
),
enriquecida AS (
    SELECT
        v.fecha, v.cliente_id, v.id_truncado, v.cod_activo, v.aba_cop,
        COALESCE(v.macroactivo, mm.macroactivo, 'Sin clasificar') AS macroactivo,
        COALESCE(v.cod_perfil_riesgo, dp.cod_perfil_riesgo)       AS cod_perfil_riesgo,
        COALESCE(v.cod_banca, db.cod_banca)                       AS cod_banca
    FROM validas v
    LEFT JOIN mapa_macro mm ON mm.cod_activo = v.cod_activo
    LEFT JOIN dim_perfil dp ON dp.cliente_id = v.cliente_id
    LEFT JOIN dim_banca  db ON db.cliente_id = v.cliente_id
)
SELECT
    e.fecha,
    e.cliente_id,
    e.id_truncado,
    e.macroactivo,
    e.cod_activo,
    CASE WHEN e.cod_activo IS NULL THEN 'SIN CLASIFICAR'
         WHEN ca.activo    IS NULL THEN 'NO CATALOGADO (' || e.cod_activo || ')'
         ELSE ca.activo
    END                                       AS activo,
    e.aba_cop,
    e.cod_perfil_riesgo,
    COALESCE(cp.perfil_riesgo, 'SIN DEFINIR') AS perfil_riesgo,
    e.cod_banca,
    COALESCE(cb.banca, 'SIN BANCA')           AS banca
FROM enriquecida e
LEFT JOIN v_cat_activos       ca ON ca.cod_activo        = e.cod_activo
LEFT JOIN v_cat_perfil_riesgo cp ON cp.cod_perfil_riesgo = e.cod_perfil_riesgo
LEFT JOIN v_cat_banca         cb ON cb.cod_banca         = e.cod_banca;


---Etapa 5
CREATE OR REPLACE VIEW v_usd_parseado AS
WITH p AS (
    SELECT
        u.*,
        CASE WHEN ingestion_year  ~ '^20[0-9]{2}$'
              AND ingestion_month ~ '^(0?[1-9]|1[0-2])$'
              AND ingestion_day   ~ '^(0?[1-9]|[12][0-9]|3[01])$'
             THEN make_date(ingestion_year::int, ingestion_month::int, 1)
                  + (ingestion_day::int - 1)
        END AS fecha_calc,
        CASE WHEN cantidad      ~ '^-?[0-9]+(\.[0-9]+)?$' THEN cantidad::numeric      END AS cantidad_num,
        CASE WHEN valor_mercado ~ '^-?[0-9]+(\.[0-9]+)?$' THEN valor_mercado::numeric END AS valor_usd,
        CASE WHEN tasa_cupon    ~ '^[0-9]+(\.[0-9]+)?$'   THEN tasa_cupon::numeric    END AS tasa_cupon_num,
        CASE WHEN fecha_vencimiento ~ '^(0?[1-9]|1[0-2])/(0?[1-9]|[12][0-9]|3[01])/[0-9]{4}$'
             THEN make_date(split_part(fecha_vencimiento, '/', 3)::int,
                            split_part(fecha_vencimiento, '/', 1)::int, 1)
                  + (split_part(fecha_vencimiento, '/', 2)::int - 1)
        END AS vencimiento_calc
    FROM historico_aba_usd_internacional u
),
q AS (
    SELECT
        p.*,
        CASE WHEN fecha_calc IS NULL THEN NULL
             WHEN EXTRACT(MONTH FROM fecha_calc) = ingestion_month::int THEN fecha_calc
        END AS fecha
    FROM p
)
SELECT
    q.*,
    COALESCE(
        fecha IS NOT NULL
        AND valor_usd    IS NOT NULL
        AND cantidad_num IS NOT NULL
        AND id_sistema_cliente ~ '^[0-9]{10,}$'
        AND nombre_activo IS NOT NULL
        AND nombre_activo !~ '^[0-9.]+$',
        false
    ) AS es_valida
FROM q;

CREATE OR REPLACE VIEW v_usd_rechazados AS
SELECT ingestion_year, ingestion_month, ingestion_day, id_sistema_cliente, simbol,
       cusip, isin, nombre_activo, cantidad, valor_mercado, fecha_vencimiento, tasa_cupon
FROM v_usd_parseado
WHERE NOT es_valida;

CREATE OR REPLACE VIEW v_usd_limpio AS
WITH base AS (
    SELECT DISTINCT
        fecha,
        id_sistema_cliente   AS cliente_id,
        simbol,
        cusip,
        isin,
        TRIM(nombre_activo)  AS nombre_activo,
        cantidad_num         AS cantidad,
        valor_usd,
        CASE WHEN vencimiento_calc IS NOT NULL
              AND EXTRACT(YEAR FROM vencimiento_calc) > 1900
             THEN vencimiento_calc END AS fecha_vencimiento,
        COALESCE(tasa_cupon_num, 0)    AS tasa_cupon
    FROM v_usd_parseado
    WHERE es_valida
)
SELECT
    b.*,
    CASE
        WHEN isin = 'Liquidez' OR cusip IN ('MONEYMRKT', 'USD999997') THEN 'Liquidez'
        WHEN fecha_vencimiento IS NOT NULL OR tasa_cupon > 0          THEN 'Renta fija'
        WHEN simbol IS NULL                                           THEN 'Fondos'
        ELSE 'Acciones y ETFs'
    END AS tipo_activo
FROM base b;


---Etapa 6

CREATE OR REPLACE VIEW v_reporte_calidad AS
SELECT
    'historico_aba_macroactivos' AS tabla,
    (SELECT COUNT(*) FROM historico_aba_macroactivos) AS filas_crudas,
    (SELECT COUNT(*) FROM v_macro_rechazados)         AS filas_rechazadas,
    (SELECT COUNT(*) FROM v_macro_parseado WHERE es_valida)
        - (SELECT COUNT(*) FROM v_macro_limpio)       AS duplicadas_removidas,
    (SELECT COUNT(*) FROM v_macro_limpio)             AS filas_limpias
UNION ALL
SELECT
    'historico_aba_usd_internacional',
    (SELECT COUNT(*) FROM historico_aba_usd_internacional),
    (SELECT COUNT(*) FROM v_usd_rechazados),
    (SELECT COUNT(*) FROM v_usd_parseado WHERE es_valida)
        - (SELECT COUNT(*) FROM v_usd_limpio),
    (SELECT COUNT(*) FROM v_usd_limpio);