-- Ejecutar después de 01_funds.sql.
CREATE TABLE [SCHEMA_PLACEHOLDER].fund_navs (
    fund_id bigint NOT NULL REFERENCES [SCHEMA_PLACEHOLDER].funds (id),
    nav_date date NOT NULL,
    nav_value numeric(80,48) NOT NULL,
    fetched_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- La clave primaria crea el índice para consultar el histórico por fondo y fecha.
    PRIMARY KEY (fund_id, nav_date),
    CONSTRAINT fund_navs_value_positive CHECK (
        nav_value > 0 AND nav_value <> 'NaN'::numeric
    )
);
