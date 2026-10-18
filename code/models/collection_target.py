"""Objetos que describen qué fondo y fuentes puede consultar el recolector."""

from dataclasses import dataclass
from datetime import date

from models.fund import Fund
from models.data_source import DataSource
from models.fund_source import FundSource


@dataclass(frozen=True, slots=True)
class CollectionSource:
    """Asociación y proveedor necesarios para construir una consulta externa."""

    # Asociación fondo-proveedor con los localizadores y la prioridad de esta ruta.
    association: FundSource
    # Proveedor y código del adaptador necesarios para consultar esta ruta.
    source: DataSource


@dataclass(frozen=True, slots=True)
class CollectionTarget:
    """Fondo con rutas ordenadas y última fecha guardada, sin garantizar continuidad."""

    # Fondo cuyos valores liquidativos se desea recoger.
    fund: Fund
    # Rutas de consulta ordenadas por prioridad y, en caso de empate, por id de asociación.
    sources: tuple[CollectionSource, ...]
    # Última fecha de valoración guardada; None si no hay histórico. No garantiza que no existan huecos.
    latest_nav_date: date | None
