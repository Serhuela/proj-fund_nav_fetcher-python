-- 03. Localización de cada fondo en sus proveedores.
-- Ejecutar después de 01_funds.sql y 02_data_sources.sql.
CREATE TABLE [SCHEMA_PLACEHOLDER].fund_sources (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fund_id bigint NOT NULL REFERENCES [SCHEMA_PLACEHOLDER].funds (id),
    source_id bigint NOT NULL REFERENCES [SCHEMA_PLACEHOLDER].data_sources (id),
    external_id text,
    nav_url text,
    priority integer NOT NULL DEFAULT 1,
    active boolean NOT NULL DEFAULT true,
    CONSTRAINT fund_sources_fund_source_unique UNIQUE (fund_id, source_id),
    -- Destino de la FK compuesta de fund_navs: impide mezclar fondos y fuentes.
    CONSTRAINT fund_sources_fund_id_id_unique UNIQUE (fund_id, id),
    CONSTRAINT fund_sources_external_id_not_empty CHECK (
        external_id IS NULL OR btrim(external_id) <> ''
    ),
    CONSTRAINT fund_sources_nav_url_not_empty CHECK (
        nav_url IS NULL OR btrim(nav_url) <> ''
    ),
    CONSTRAINT fund_sources_priority_positive CHECK (priority > 0)
);

CREATE INDEX fund_sources_source_id_idx
    ON [SCHEMA_PLACEHOLDER].fund_sources (source_id);

COMMENT ON TABLE [SCHEMA_PLACEHOLDER].fund_sources IS
    'Asociación única entre un fondo y un proveedor de valores liquidativos.';
COMMENT ON COLUMN [SCHEMA_PLACEHOLDER].fund_sources.external_id IS
    'Identificador del proveedor si no basta con el ISIN; NULL cuando no sea necesario.';
COMMENT ON COLUMN [SCHEMA_PLACEHOLDER].fund_sources.nav_url IS
    'URL específica de consulta de valores, no la del folleto; NULL si el adaptador puede construirla. Sin secretos.';
COMMENT ON COLUMN [SCHEMA_PLACEHOLDER].fund_sources.priority IS
    'Menor número implica mayor preferencia. En empates, la aplicación ordena por id.';
COMMENT ON COLUMN [SCHEMA_PLACEHOLDER].fund_sources.active IS
    'Habilita esta ruta de consulta; fondo y proveedor también deben estar activos.';
