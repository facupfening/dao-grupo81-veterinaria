from dao.catalogo_dao import CatalogoDAO
from dao.vacuna_dao import VacunaDAO
from negocio.gestor import Gestor


class GestorCatalogos(Gestor):
    """Datos de referencia para completar las listas de opciones de las pantallas."""

    def listar_especies(self):
        with self._transaccion() as conexion:
            return CatalogoDAO(conexion).listar_especies()

    def listar_clinicas(self):
        with self._transaccion() as conexion:
            return CatalogoDAO(conexion).listar_clinicas()

    def listar_veterinarios(self):
        with self._transaccion() as conexion:
            return CatalogoDAO(conexion).listar_veterinarios()

    def listar_laboratorios(self):
        with self._transaccion() as conexion:
            return CatalogoDAO(conexion).listar_laboratorios()

    def listar_tipos_analisis(self):
        with self._transaccion() as conexion:
            return CatalogoDAO(conexion).listar_tipos_analisis()

    def listar_transportistas(self):
        with self._transaccion() as conexion:
            return CatalogoDAO(conexion).listar_transportistas()

    def listar_vacunas_por_especie(self, especie_id):
        with self._transaccion() as conexion:
            return VacunaDAO(conexion).listar_por_especie(especie_id)
