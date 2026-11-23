-- Composición del portafolio local (COP), en % del total del cliente
CREATE OR REPLACE VIEW v_mix_local AS
SELECT
    cliente_id,
    COALESCE(100.0 * SUM(valor_cop) FILTER (WHERE macroactivo ILIKE 'renta variable')
             / NULLIF(SUM(valor_cop), 0), 0) AS pct_rv_cop,
    COALESCE(100.0 * SUM(valor_cop) FILTER (WHERE macroactivo ILIKE 'fics')
             / NULLIF(SUM(valor_cop), 0), 0) AS pct_fic_cop,
    COALESCE(100.0 * SUM(valor_cop) FILTER (WHERE macroactivo ILIKE 'renta fija')
             / NULLIF(SUM(valor_cop), 0), 0) AS pct_rf_cop
FROM v_portafolio_local_ultimo
GROUP BY cliente_id;

-- Composición del portafolio internacional (USD)
CREATE OR REPLACE VIEW v_mix_usd AS
SELECT
    cliente_id,
    COALESCE(100.0 * SUM(valor_usd) FILTER (WHERE tipo_activo ILIKE 'acciones%')
             / NULLIF(SUM(valor_usd), 0), 0) AS pct_acciones_usd,
    COALESCE(100.0 * SUM(valor_usd) FILTER (WHERE tipo_activo ILIKE 'renta fija')
             / NULLIF(SUM(valor_usd), 0), 0) AS pct_rf_usd,
    COALESCE(100.0 * SUM(valor_usd) FILTER (WHERE tipo_activo ILIKE 'fondos')
             / NULLIF(SUM(valor_usd), 0), 0) AS pct_fondos_usd,
    COALESCE(100.0 * SUM(valor_usd) FILTER (WHERE tipo_activo ILIKE 'liquidez')
             / NULLIF(SUM(valor_usd), 0), 0) AS pct_liquidez_usd
FROM v_portafolio_usd_ultimo
GROUP BY cliente_id;

-- Tabla final: una fila por cliente, lista para el modelo
CREATE OR REPLACE VIEW v_modelo_clientes AS
SELECT f.*,
       m.pct_rv_cop, m.pct_fic_cop, m.pct_rf_cop,
       u.pct_acciones_usd, u.pct_rf_usd, u.pct_fondos_usd, u.pct_liquidez_usd
FROM v_features_cliente f
LEFT JOIN v_mix_local m USING (cliente_id)
LEFT JOIN v_mix_usd   u USING (cliente_id);