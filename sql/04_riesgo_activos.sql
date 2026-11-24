-- Riesgo por activo (escala 1 = muy bajo ... 5 = muy alto).
-- Fuente de verdad: ESTE archivo. Para cambiar un valor, edítalo aquí y vuelve a ejecutarlo.

DROP VIEW  IF EXISTS v_cliente_features;
DROP VIEW  IF EXISTS v_riesgo_local_cliente;
DROP VIEW  IF EXISTS v_riesgo_usd_cliente;
DROP VIEW  IF EXISTS v_riesgo_usd_posicion;
DROP TABLE IF EXISTS riesgo_clase_local;
DROP TABLE IF EXISTS riesgo_activo_local;
DROP TABLE IF EXISTS riesgo_usd_manual;

-- 1) Riesgo por defecto según la clase (para activos sin ficha)
CREATE TABLE riesgo_clase_local (
    macroactivo TEXT PRIMARY KEY,
    riesgo      NUMERIC(2,1) NOT NULL
);
INSERT INTO riesgo_clase_local VALUES
    ('Renta Fija',     1.5),
    ('FICs',           2.5),
    ('Renta Variable', 4.5);

-- 2) Riesgo por activo local (sale de tus fichas; los marcados 'provisional' se ajustan al investigar)
CREATE TABLE riesgo_activo_local (
    cod_activo TEXT PRIMARY KEY,
    riesgo     NUMERIC(2,1) NOT NULL,
    fuente     TEXT
);
INSERT INTO riesgo_activo_local VALUES
    ('1019', 1.0, 'Ficha técnica Renta Liquidez 31/10/2026: AAAf/S1, vol 0,226 %'),
    ('1007', 1.0, 'Ficha técnica Fiducuenta 31/10/2026: S1/AAAf, vol 0,404 %'),
    ('1000', 1.0, 'CDT Bancolombia: AAA(col) Fitch 12/11/2026; seguro Fogafín'),
    ('1001', 1.5, 'CDT Tuya: AAA(col) Fitch 12/11/2026; compañía de financiamiento, sobre tope Fogafín'),
    ('1008', 1.5, 'Ficha técnica Fidurenta 31/10/2026: S2/AAAf, vol 0,799 %'),
    ('1018', 2.0, 'Ficha técnica Plan Semilla 31/10/2026: S3/AAAf, vol 1,315 %'),
    ('1020', 3.0, 'Ficha FIC Sura Crédito Privado 31/10/2026: cerrado, sin calificación, activos alternativos');

-- 3) Correcciones manuales USD por ISIN (vacía al inicio; tiene prioridad sobre las reglas)
CREATE TABLE riesgo_usd_manual (
    isin   TEXT PRIMARY KEY,
    riesgo NUMERIC(2,1) NOT NULL,
    fuente TEXT
);

-- 4) Riesgo por posición USD: manual > reglas por nombre > valor por tipo
CREATE VIEW v_riesgo_usd_posicion AS
SELECT
    p.cliente_id,
    p.tipo_activo,
    p.nombre_activo,
    p.isin,
    p.valor_usd,
    COALESCE(m.riesgo,
        CASE
            WHEN p.tipo_activo = 'Liquidez'                                         THEN 1.0
            WHEN p.nombre_activo ILIKE '%3X%'                                       THEN 5.0  -- ETF apalancado
            WHEN p.nombre_activo ~* '(LKD|LNKD|TWIN-WIN|AUTOCALL)'                  THEN 3.5  -- nota estructurada
            WHEN p.nombre_activo ILIKE '%UNITED STATES TREAS%'                      THEN 1.0  -- Tesoro EE.UU.
            WHEN p.tipo_activo = 'Acciones y ETFs'
                 AND p.nombre_activo ~* '(TREAS|BOND|SHORT DURATION)'            THEN 1.5  -- ETF de bonos
            WHEN p.tipo_activo = 'Renta fija'                                       THEN 2.0  -- bono corporativo
            WHEN p.tipo_activo = 'Fondos'
                 AND p.nombre_activo ~* '(BOND|FIXED INCOME)'                       THEN 2.0  -- fondo de bonos
            WHEN p.tipo_activo = 'Fondos'
                 AND p.nombre_activo ~* '(EQUITY|TECHNOLOGY|ASIA|EMERGING|U\.S\. OPPORTUNITIES|GROWTH|FRANCHISE|INFRASTRUCTURE)'
                                                                                     THEN 4.0  -- fondo de acciones
            WHEN p.tipo_activo = 'Fondos'                                           THEN 3.0  -- mixtos / multiactivo
            WHEN p.tipo_activo = 'Acciones y ETFs'                                  THEN 4.0
            ELSE 3.0
        END) AS riesgo
FROM v_portafolio_usd_ultimo p
LEFT JOIN riesgo_usd_manual m ON m.isin = p.isin;

-- 5) Puntaje de riesgo ponderado por cliente (solo saldos positivos)
CREATE VIEW v_riesgo_usd_cliente AS
SELECT cliente_id,
       SUM(GREATEST(valor_usd, 0) * riesgo) / NULLIF(SUM(GREATEST(valor_usd, 0)), 0) AS score_usd
FROM v_riesgo_usd_posicion
GROUP BY cliente_id;

CREATE VIEW v_riesgo_local_cliente AS
SELECT p.cliente_id,
       SUM(GREATEST(p.valor_cop, 0) * COALESCE(a.riesgo, c.riesgo, 2.5))
         / NULLIF(SUM(GREATEST(p.valor_cop, 0)), 0) AS score_cop
FROM v_portafolio_local_ultimo p
LEFT JOIN riesgo_activo_local a ON a.cod_activo = p.cod_activo::text
LEFT JOIN riesgo_clase_local  c ON c.macroactivo = p.macroactivo
GROUP BY p.cliente_id;