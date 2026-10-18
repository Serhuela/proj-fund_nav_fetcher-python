"""Objeto de datos para DataSource, sin acceso a la base de datos."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DataSource:
    """Proveedor de datos y código del adaptador que lo consulta."""

    # Identificador del proveedor en la base de datos.
    id: int
    # Código estable que identifica el adaptador Python encargado de consultar al proveedor.
    code: str
    # Nombre del proveedor de datos.
    name: str
    # URL base pública del proveedor o de su API, sin credenciales.
    base_url: str
    # Indica si se permiten consultas al proveedor; desactivarlo conserva asociaciones e histórico.
    active: bool = True
