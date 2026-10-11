-- 04. Un valor liquidativo seleccionado por fondo y fecha, con su procedencia.
-- Ejecutar después de 03_fund_sources.sql.
CREATE TABLE [SCHEMA_PLACEHOLDER].fund_navs (
    fund_id bigint NOT NULL,
    nav_date date NOT NULL,
    nav_value numeric(80,48) NOT NULL,
    fund_source_id bigint NOT NULL,
    fetched_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- También permite consultar el histórico de cada fondo por fecha.
    PRIMARY KEY (fund_id, nav_date),
    CONSTRAINT fund_navs_fund_source_fk FOREIGN KEY (fund_id, fund_source_id)
        REFERENCES [SCHEMA_PLACEHOLDER].fund_sources (fund_id, id),
    CONSTRAINT fund_navs_value_positive CHECK (
        nav_value > 0 AND nav_value <> 'NaN'::numeric
    )
);

CREATE INDEX fund_navs_fund_source_idx
    ON [SCHEMA_PLACEHOLDER].fund_navs (fund_id, fund_source_id);

COMMENT ON TABLE [SCHEMA_PLACEHOLDER].fund_navs IS
    'Un NAV por fondo y fecha. No almacena observaciones simultáneas de varios proveedores ni versiones de correcciones.';
COMMENT ON COLUMN [SCHEMA_PLACEHOLDER].fund_navs.nav_date IS
    'Fecha de valoración publicada por la fuente, no la fecha de descarga.';
COMMENT ON COLUMN [SCHEMA_PLACEHOLDER].fund_navs.nav_value IS
    'Valor liquidativo positivo expresado en funds.currency; conservar como Decimal en Python.';
COMMENT ON COLUMN [SCHEMA_PLACEHOLDER].fund_navs.fund_source_id IS
    'Origen del valor guardado. La FK compuesta exige que corresponda al mismo fondo.';
COMMENT ON COLUMN [SCHEMA_PLACEHOLDER].fund_navs.fetched_at IS
    'Instante de recogida del valor almacenado; la aplicación debe actualizarlo al sustituir un NAV corregido.';
