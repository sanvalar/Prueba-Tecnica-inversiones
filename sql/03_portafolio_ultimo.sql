---Etapa 7
CREATE OR REPLACE VIEW v_portafolio_local_ultimo AS
WITH ultima AS (
    SELECT cliente_id, MAX(fecha) AS fecha
    FROM v_macro_limpio
    GROUP BY cliente_id
),
posiciones AS (
    SELECT
        m.cliente_id, m.fecha, m.macroactivo, m.cod_activo, m.activo,
        SUM(m.aba_cop)         AS valor_cop,
        MAX(m.perfil_riesgo)   AS perfil_riesgo,
        MAX(m.banca)           AS banca,
        BOOL_OR(m.id_truncado) AS id_truncado
    FROM v_macro_limpio m
    JOIN ultima u ON u.cliente_id = m.cliente_id AND u.fecha = m.fecha
    GROUP BY m.cliente_id, m.fecha, m.macroactivo, m.cod_activo, m.activo
)
SELECT
    p.*,
    ROUND(100 * p.valor_cop / NULLIF(SUM(p.valor_cop) OVER (PARTITION BY p.cliente_id), 0), 2)
        AS participacion_pct
FROM posiciones p;

CREATE OR REPLACE VIEW v_portafolio_usd_ultimo AS
WITH ultima AS (
    SELECT cliente_id, MAX(fecha) AS fecha
    FROM v_usd_limpio
    GROUP BY cliente_id
),
posiciones AS (
    SELECT
        u.cliente_id, u.fecha, u.tipo_activo, u.isin, u.nombre_activo,
        MAX(u.simbol)            AS simbol,
        MAX(u.fecha_vencimiento) AS fecha_vencimiento,
        MAX(u.tasa_cupon)        AS tasa_cupon,
        SUM(u.cantidad)          AS cantidad,
        SUM(u.valor_usd)         AS valor_usd
    FROM v_usd_limpio u
    JOIN ultima x ON x.cliente_id = u.cliente_id AND x.fecha = u.fecha
    GROUP BY u.cliente_id, u.fecha, u.tipo_activo, u.isin, u.nombre_activo
)
SELECT
    p.*,
    ROUND(100 * p.valor_usd / NULLIF(SUM(p.valor_usd) OVER (PARTITION BY p.cliente_id), 0), 2)
        AS participacion_pct
FROM posiciones p;



---Etapa 8
CREATE OR REPLACE VIEW v_cliente_resumen AS
WITH loc AS (
    SELECT
        cliente_id,
        MAX(fecha)             AS fecha_cop,
        MAX(perfil_riesgo)     AS perfil_riesgo,
        MAX(banca)             AS banca,
        BOOL_OR(id_truncado)   AS id_truncado,
        SUM(valor_cop)         AS total_cop,
        COUNT(*)               AS n_posiciones_cop,
        MAX(participacion_pct) AS concentracion_max_cop,
        SUM(CASE WHEN macroactivo = 'Renta Fija'     THEN valor_cop ELSE 0 END) AS cop_renta_fija,
        SUM(CASE WHEN macroactivo = 'Renta Variable' THEN valor_cop ELSE 0 END) AS cop_renta_variable,
        SUM(CASE WHEN macroactivo = 'FICs'           THEN valor_cop ELSE 0 END) AS cop_fics
    FROM v_portafolio_local_ultimo
    GROUP BY cliente_id
),
intl AS (
    SELECT
        cliente_id,
        MAX(fecha)     AS fecha_usd,
        SUM(valor_usd) AS total_usd,
        COUNT(*)       AS n_posiciones_usd,
        SUM(CASE WHEN tipo_activo = 'Liquidez'        THEN valor_usd ELSE 0 END) AS usd_liquidez,
        SUM(CASE WHEN tipo_activo = 'Renta fija'      THEN valor_usd ELSE 0 END) AS usd_renta_fija,
        SUM(CASE WHEN tipo_activo = 'Fondos'          THEN valor_usd ELSE 0 END) AS usd_fondos,
        SUM(CASE WHEN tipo_activo = 'Acciones y ETFs' THEN valor_usd ELSE 0 END) AS usd_acciones_etfs
    FROM v_portafolio_usd_ultimo
    GROUP BY cliente_id
)
SELECT
    COALESCE(l.cliente_id, u.cliente_id) AS cliente_id,
    l.id_truncado, l.banca, l.perfil_riesgo,
    l.fecha_cop, l.total_cop, l.n_posiciones_cop, l.concentracion_max_cop,
    l.cop_renta_fija, l.cop_renta_variable, l.cop_fics,
    u.fecha_usd, u.total_usd, u.n_posiciones_usd,
    u.usd_liquidez, u.usd_renta_fija, u.usd_fondos, u.usd_acciones_etfs,
    (u.cliente_id IS NOT NULL) AS tiene_portafolio_usd
FROM loc l
FULL JOIN intl u ON u.cliente_id = l.cliente_id;