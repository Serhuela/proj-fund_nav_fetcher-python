-- 02. Proveedores de valores liquidativos. No depende de otras tablas.
-- Sustituir [SCHEMA_PLACEHOLDER] por el esquema existente antes de ejecutar.
CREATE TABLE [SCHEMA_PLACEHOLDER].data_sources (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code text NOT NULL UNIQUE,
    name text NOT NULL,
    base_url text NOT NULL,
    active boolean NOT NULL DEFAULT true,
    CONSTRAINT data_sources_code_format CHECK (code ~ '^[a-z][a-z0-9_]*$'),
    CONSTRAINT data_sources_name_not_empty CHECK (btrim(name) <> ''),
    CONSTRAINT data_sources_base_url_not_empty CHECK (btrim(base_url) <> '')
);

COMMENT ON TABLE [SCHEMA_PLACEHOLDER].data_sources IS
    'Proveedores de datos, independientes de las entidades que comercializan el fondo.';
COMMENT ON COLUMN [SCHEMA_PLACEHOLDER].data_sources.code IS
    'Código estable que identifica el adaptador Python, por ejemplo amundi.';
COMMENT ON COLUMN [SCHEMA_PLACEHOLDER].data_sources.base_url IS
    'Dirección base pública del proveedor o de su API; no debe contener credenciales.';
COMMENT ON COLUMN [SCHEMA_PLACEHOLDER].data_sources.active IS
    'Permite detener las consultas a un proveedor conservando sus asociaciones e histórico.';
