import sqlite3
from contextlib import contextmanager
from pathlib import Path

CARPETA_DATOS = Path(__file__).parent
RUTA_DB = CARPETA_DATOS.parent / "veterinaria.db"


def conectar(ruta=RUTA_DB):
    """Abre una conexión con las claves foráneas activadas y filas accesibles por nombre."""
    conexion = sqlite3.connect(ruta)
    conexion.row_factory = sqlite3.Row
    # SQLite no controla las claves foráneas salvo que se active en cada conexión.
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


@contextmanager
def transaccion(ruta=RUTA_DB):
    """Agrupa varias operaciones: confirma todo al terminar o deshace todo ante un error."""
    conexion = conectar(ruta)
    try:
        yield conexion
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def crear_tablas(conexion):
    """Crea las tablas y los triggers que todavía no existan."""
    _ejecutar_script(conexion, "esquema.sql")


def cargar_datos_ejemplo(conexion):
    """Carga los datos de ejemplo. Devuelve False si la base ya tenía datos."""
    cantidad = conexion.execute("SELECT COUNT(*) FROM especies").fetchone()[0]
    if cantidad > 0:
        return False
    _ejecutar_script(conexion, "datos_ejemplo.sql")
    return True


def inicializar(ruta=RUTA_DB):
    """Deja la base lista para usar: crea lo que falte y carga los datos de ejemplo."""
    conexion = conectar(ruta)
    try:
        crear_tablas(conexion)
        cargar_datos_ejemplo(conexion)
    finally:
        conexion.close()


def _ejecutar_script(conexion, nombre_archivo):
    script = (CARPETA_DATOS / nombre_archivo).read_text(encoding="utf-8")
    conexion.executescript(script)
