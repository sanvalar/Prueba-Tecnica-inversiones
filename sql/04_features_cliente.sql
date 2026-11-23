CREATE OR REPLACE VIEW v_features_cliente AS
WITH loc AS (
    SELECT cliente_id,
           COUNT(*)                                  AS n_activos_cop,
           COUNT(DISTINCT macroactivo)               AS n_macroactivos_cop,
           MAX(participacion_pct)                    AS max_part_cop,
           SUM(POWER(participacion_pct / 100.0, 2))  AS hhi_cop
    FROM v_portafolio_local_ultimo
    GROUP BY cliente_id
),
usd AS (
    SELECT cliente_id,
           COUNT(*)                                  AS n_activos_usd,
           COUNT(DISTINCT tipo_activo)               AS n_tipos_usd,
           MAX(participacion_pct)                    AS max_part_usd,
           SUM(POWER(participacion_pct / 100.0, 2))  AS hhi_usd
    FROM v_portafolio_usd_ultimo
    GROUP BY cliente_id
)
SELECT r.cliente_id,
       r.banca,
       r.perfil_riesgo,
       r.id_truncado,
       r.tiene_portafolio_usd,
       r.fecha_cop,
       r.fecha_usd,
       r.total_cop,
       r.total_usd,
       COALESCE(l.n_activos_cop, 0)       AS n_activos_cop,
       COALESCE(l.n_macroactivos_cop, 0)  AS n_macroactivos_cop,
       l.max_part_cop,
       l.hhi_cop,
       COALESCE(u.n_activos_usd, 0)       AS n_activos_usd,
       COALESCE(u.n_tipos_usd, 0)         AS n_tipos_usd,
       u.max_part_usd,
       u.hhi_usd
FROM v_cliente_resumen r
LEFT JOIN loc l USING (cliente_id)
LEFT JOIN usd u USING (cliente_id);