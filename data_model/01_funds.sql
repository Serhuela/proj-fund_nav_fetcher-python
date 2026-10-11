-- 01. Fondos identificados por ISIN. No depende de otras tablas.
-- Sustituir [SCHEMA_PLACEHOLDER] por el esquema existente antes de ejecutar.
CREATE TABLE [SCHEMA_PLACEHOLDER].funds (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    isin varchar(12) NOT NULL UNIQUE,
    name text NOT NULL,
    currency varchar(3) NOT NULL,
    active boolean NOT NULL DEFAULT true,
    CONSTRAINT funds_isin_format CHECK (isin ~ '^[A-Z]{2}[A-Z0-9]{9}[0-9]$'),
    CONSTRAINT funds_name_not_empty CHECK (btrim(name) <> ''),
    CONSTRAINT funds_currency_format CHECK (currency ~ '^[A-Z]{3}$')
);

COMMENT ON TABLE [SCHEMA_PLACEHOLDER].funds IS
    'Fondos que se desean seguir; pueden existir antes de configurar sus fuentes.';
COMMENT ON COLUMN [SCHEMA_PLACEHOLDER].funds.isin IS
    'Identifica de forma única el fondo. El formato se valida aquí; el dígito de control, no.';
COMMENT ON COLUMN [SCHEMA_PLACEHOLDER].funds.currency IS
    'Divisa del valor liquidativo. La aplicación debe contrastarla con la respuesta del proveedor.';
COMMENT ON COLUMN [SCHEMA_PLACEHOLDER].funds.active IS
    'Habilita la recogida del fondo sin eliminar su histórico.';
