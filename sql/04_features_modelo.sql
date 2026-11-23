DROP VIEW IF EXISTS v_cliente_features;

CREATE VIEW v_cliente_features AS
SELECT
    cliente_id,
    id_truncado,
    banca,
    perfil_riesgo,
    fecha_cop,
    total_cop,
    n_posiciones_cop,
    concentracion_max_cop,
    cop_renta_fija,
    cop_renta_variable,
    cop_fics,
    fecha_usd,
    total_usd,
    usd_liquidez,
    usd_renta_fija,
    usd_fondos,
    usd_acciones_etfs,
    tiene_portafolio_usd
FROM v_cliente_resumen;