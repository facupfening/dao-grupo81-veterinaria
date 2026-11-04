from dao.catalogo_dao import CatalogoDAO
from dao.cliente_dao import ClienteDAO
from dao.consulta_dao import ConsultaDAO
from dao.mascota_dao import MascotaDAO
from dao.muestra_dao import MuestraDAO
from dao.orden_dao import OrdenDAO
from dao.vacuna_dao import VacunaDAO
from modelos.mascota import Mascota
from modelos.validaciones import validar_fecha_hora
from negocio.gestor import ErrorNegocio, Gestor


class GestorMascotas(Gestor):
    def alta(self, cliente_id, especie_id, nombre, fecha_apertura, raza=None, sexo=None,
             fecha_nacimiento=None, peso_kg=None, antecedentes=None):
        """Registra la mascota y le abre su historia clínica, todo o nada."""
        with self._transaccion() as conexion:
            validar_fecha_hora(fecha_apertura, "Fecha de apertura")
            mascota = Mascota(cliente_id, especie_id, nombre, raza, sexo, fecha_nacimiento, peso_kg)
            self._verificar_referencias(conexion, mascota)
            dao = MascotaDAO(conexion)
            dao.crear(mascota)
            dao.crear_historia(mascota.id, fecha_apertura, antecedentes)
            return mascota.id

    def modificar(self, id, cliente_id, especie_id, nombre, raza=None, sexo=None,
                  fecha_nacimiento=None, peso_kg=None):
        with self._transaccion() as conexion:
            dao = MascotaDAO(conexion)
            self._exigir(dao.obtener_por_id(id), "La mascota no existe")
            mascota = Mascota(cliente_id, especie_id, nombre, raza, sexo, fecha_nacimiento, peso_kg, id)
            self._verificar_referencias(conexion, mascota)
            dao.actualizar(mascota)

    def actualizar_antecedentes(self, id, antecedentes):
        with self._transaccion() as conexion:
            dao = MascotaDAO(conexion)
            self._exigir(dao.obtener_por_id(id), "La mascota no existe")
            dao.actualizar_antecedentes(id, antecedentes)

    def baja(self, id):
        """Solo se puede borrar una mascota sin turnos ni consultas, para no perder trazabilidad."""
        with self._transaccion() as conexion:
            dao = MascotaDAO(conexion)
            self._exigir(dao.obtener_por_id(id), "La mascota no existe")
            if dao.tiene_atenciones(id):
                raise ErrorNegocio("No se puede dar de baja una mascota con turnos o consultas registrados")
            dao.eliminar_historia(id)
            dao.eliminar(id)

    def obtener(self, id):
        with self._transaccion() as conexion:
            return MascotaDAO(conexion).obtener_por_id(id)

    def listar(self):
        with self._transaccion() as conexion:
            return MascotaDAO(conexion).listar()

    def listar_detallado(self):
        with self._transaccion() as conexion:
            return MascotaDAO(conexion).listar_detallado()

    def listar_por_cliente(self, cliente_id):
        with self._transaccion() as conexion:
            return MascotaDAO(conexion).listar_por_cliente(cliente_id)

    def obtener_historia(self, id):
        """Reúne las consultas, vacunas, órdenes, muestras y resultados de la mascota."""
        with self._transaccion() as conexion:
            historia = self._exigir(MascotaDAO(conexion).obtener_historia(id), "La mascota no existe")
            ordenes = []
            muestra_dao = MuestraDAO(conexion)
            for orden in OrdenDAO(conexion).listar_por_historia(historia["id"]):
                muestras = [
                    {"muestra": muestra, "resultado": muestra_dao.obtener_resultado(muestra.id)}
                    for muestra in muestra_dao.listar_por_orden(orden["id"])
                ]
                ordenes.append({"orden": orden, "muestras": muestras})
            return {
                "historia": historia,
                "consultas": ConsultaDAO(conexion).listar_por_historia(historia["id"]),
                "vacunas": VacunaDAO(conexion).listar_aplicaciones_por_historia(historia["id"]),
                "ordenes": ordenes,
            }

    def _verificar_referencias(self, conexion, mascota):
        self._exigir(ClienteDAO(conexion).obtener_por_id(mascota.cliente_id), "El cliente responsable no existe")
        self._exigir(CatalogoDAO(conexion).obtener_especie(mascota.especie_id), "La especie no existe")
