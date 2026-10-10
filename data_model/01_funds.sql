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
