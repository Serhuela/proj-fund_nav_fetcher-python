"""Objeto de datos para Fund, sin acceso a la base de datos."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Fund:
    """Fondo identificado por su ISIN; id es el identificador persistido."""

    # Identificador del fondo en la base de datos.
    id: int
    # Código ISIN que identifica de forma única el fondo.
    isin: str
    # Nombre del fondo.
    name: str
    # Código de tres letras de la divisa en la que se expresa el valor liquidativo.
    currency: str
    # Indica si está habilitada la recogida del fondo; desactivarlo conserva su histórico.
    active: bool = True
