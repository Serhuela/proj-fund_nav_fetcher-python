"""Pruebas unitarias de code/app/main.py.

Cubre que main() delega una sola vez en el arranque común.
No cubre la lógica de application.run(), el arranque del contenedor ni la
ejecución del módulo desde la línea de comandos.
"""

from unittest.mock import Mock

import pytest

from app import main


def test_main_inicia_la_aplicacion_una_vez(monkeypatch: pytest.MonkeyPatch) -> None:
    """Comprueba la delegación sin ejecutar el bucle de la aplicación."""
    arranque = Mock()
    monkeypatch.setattr(main, "run", arranque)

    main.main()

    arranque.assert_called_once_with()
