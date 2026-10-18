"""Objeto de datos para FundNav, sin acceso a la base de datos."""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class FundNav:
    """NAV persistido: valor decimal, fecha de valoración y recogida normalizada a UTC."""

    # Identificador del fondo al que corresponde el valor liquidativo.
    fund_id: int
    # Fecha de valoración publicada por la fuente, independiente de la fecha de recogida.
    nav_date: date
    # Valor liquidativo expresado como Decimal en la divisa del fondo.
    nav_value: Decimal
    # Identificador de la asociación fondo-proveedor de la que procede el valor guardado.
    fund_source_id: int
    # Instante de recogida con zona horaria; se normaliza a UTC al crear el objeto.
    fetched_at: datetime

    def __post_init__(self) -> None:
        """Convierte la recogida a UTC conservando el instante y nav_date.

        Raises:
            ValueError: Si fetched_at no es un datetime con zona horaria.
        """
        if (
            not isinstance(self.fetched_at, datetime)
            or self.fetched_at.utcoffset() is None
        ):
            raise ValueError("La fecha de recogida debe incluir zona horaria.")
        object.__setattr__(self, "fetched_at", self.fetched_at.astimezone(timezone.utc))
