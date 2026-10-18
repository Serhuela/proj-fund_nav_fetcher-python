"""Objeto de datos para FundSource, sin acceso a la base de datos."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FundSource:
    """Ruta de consulta de un fondo; localizadores opcionales y prioridad positiva."""

    # Identificador de la asociación entre fondo y proveedor en la base de datos.
    id: int
    # Identificador del fondo al que pertenece esta ruta de consulta.
    fund_id: int
    # Identificador del proveedor que ofrece los valores liquidativos del fondo.
    source_id: int
    # Identificador del fondo en el proveedor; None si basta con el ISIN.
    external_id: str | None = None
    # URL específica de consulta del valor liquidativo, sin secretos; None si el adaptador la construye.
    nav_url: str | None = None
    # Orden de preferencia: menor número positivo implica mayor preferencia; los empates se ordenan por id.
    priority: int = 1
    # Habilita esta ruta de consulta; el fondo y el proveedor también deben estar activos.
    active: bool = True
