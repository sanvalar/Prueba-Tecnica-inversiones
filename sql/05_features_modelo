CREATE VIEW v_cliente_features AS
SELECT
    r.cliente_id, r.id_truncado, r.banca, r.perfil_riesgo,
    r.fecha_cop, r.total_cop, r.n_posiciones_cop, r.concentracion_max_cop,
    r.cop_renta_fija, r.cop_renta_variable, r.cop_fics,
    r.fecha_usd, r.total_usd, r.usd_liquidez, r.usd_renta_fija, r.usd_fondos, r.usd_acciones_etfs,
    r.tiene_portafolio_usd,
    lc.score_cop,
    uc.score_usd
FROM v_cliente_resumen r
LEFT JOIN v_riesgo_local_cliente lc ON lc.cliente_id = r.cliente_id
LEFT JOIN v_riesgo_usd_cliente   uc ON uc.cliente_id = r.cliente_id;