"""Conexión PostgreSQL compartida, sin confirmaciones implícitas de escrituras."""

from typing import Any

import psycopg
from psycopg.abc import Params, Query
from psycopg.rows import dict_row

from utils.custom_logging import get_logger


logger = get_logger(__name__)


class Postgres:
    """Ejecuta SQL en una conexión transaccional de uso secuencial.

    La composición crea y cierra esta instancia; DataService decide cuándo
    confirmar o revertir. No compartirla entre operaciones concurrentes ni
    acumular escrituras ajenas antes de invocar el servicio.
    """

    def __init__(self, conninfo: str = "", **parameters: Any) -> None:
        """Abre la conexión con parámetros de Psycopg y fuerza autocommit=False.

        Las credenciales se reciben del llamador, nunca se registran. Los errores
        de conexión se propagan como excepciones de Psycopg.
        """
        parameters["autocommit"] = False
        logger.debug("Abriendo conexión PostgreSQL transaccional.")
        try:
            self._connection = psycopg.connect(conninfo, **parameters)
        except psycopg.Error as error:
            # El mensaje del controlador puede incluir credenciales o el DSN.
            logger.error("No se pudo abrir la conexión PostgreSQL (%s).", type(error).__name__)
            raise
        logger.debug("Conexión PostgreSQL abierta.")

    def execute(self, query: Query, parameters: Params | None = None) -> dict[str, Any] | None:
        """Ejecuta SQL parametrizado y devuelve la primera fila, si la hay.

        Cierra el cursor, pero no la conexión ni la transacción. Esta primitiva
        sirve para operaciones sin resultado o con una sola fila; no es una API
        de listado. Propaga los errores de Psycopg al repositorio o servicio.
        """
        logger.debug("Ejecutando consulta PostgreSQL sin confirmar la transacción.")
        with self._connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query, parameters)
            return cursor.fetchone() if cursor.description is not None else None

    def fetch_all(self, query: Query, parameters: Params | None = None) -> list[dict[str, Any]]:
        """Ejecuta una consulta y devuelve todas sus filas como mapas."""
        logger.debug("Consultando filas PostgreSQL.")
        with self._connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query, parameters)
            return cursor.fetchall()

    def execute_script(self, query: str) -> None:
        """Ejecuta un script SQL sin parámetros dentro de la transacción actual."""
        logger.debug("Ejecutando script SQL PostgreSQL.")
        with self._connection.cursor() as cursor:
            cursor.execute(query)

    def copy_rows(self, query: Query, rows: Any) -> None:
        """Copia filas ya parseadas usando el protocolo COPY de Psycopg."""
        logger.debug("Importando filas PostgreSQL mediante COPY.")
        with self._connection.cursor() as cursor:
            with cursor.copy(query) as copy:
                for row in rows:
                    copy.write_row(row)

    def commit(self) -> None:
        """Confirma la transacción actual; propaga errores de Psycopg."""
        self._connection.commit()
        logger.debug("Transacción PostgreSQL confirmada.")

    def rollback(self) -> None:
        """Revierte la transacción actual; propaga errores de Psycopg."""
        self._connection.rollback()
        logger.debug("Transacción PostgreSQL revertida.")

    def close(self) -> None:
        """Cierra la conexión sin confirmar cambios pendientes; es idempotente."""
        self._connection.close()
        logger.debug("Conexión PostgreSQL cerrada.")
