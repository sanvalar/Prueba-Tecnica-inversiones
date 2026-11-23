CREATE OR REPLACE VIEW v_estado_usd AS
SELECT cliente_id,
       CASE
           WHEN tiene_portafolio_usd THEN 'CON_USD'
           WHEN id_truncado          THEN 'NO_DETERMINABLE'
           ELSE                           'SIN_USD_CONFIRMADO'
       END AS estado_usd
FROM v_cliente_resumen;