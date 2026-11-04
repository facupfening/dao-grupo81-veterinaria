import sqlite3
from contextlib import contextmanager

from datos.base_datos import RUTA_DB, transaccion
from estados.transicion_invalida import TransicionInvalida


class ErrorNegocio(Exception):
    """Error con un mensaje apto para mostrarle al usuario."""


class Gestor:
    """Base de los gestores: cada operación del negocio es una transacción con su propia conexión."""

    def __init__(self, ruta=RUTA_DB):
        self._ruta = ruta

    @contextmanager
    def _transaccion(self):
        try:
            with transaccion(self._ruta) as conexion:
                yield conexion
        except (sqlite3.IntegrityError, TransicionInvalida, ValueError) as error:
            raise ErrorNegocio(str(error)) from error

    def _exigir(self, valor, mensaje):
        if not valor:
            raise ErrorNegocio(mensaje)
        return valor
