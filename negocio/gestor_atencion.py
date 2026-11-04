from datetime import datetime, timedelta

from dao.catalogo_dao import CatalogoDAO
from dao.consulta_dao import ConsultaDAO
from dao.mascota_dao import MascotaDAO
from dao.muestra_dao import MuestraDAO
from dao.orden_dao import OrdenDAO
from dao.turno_dao import TurnoDAO
from dao.vacuna_dao import VacunaDAO
from modelos.muestra import Muestra
from modelos.validaciones import FORMATO_FECHA_HORA, validar_fecha_hora, validar_obligatorio
from negocio.gestor import ErrorNegocio, Gestor

TIPOS_CONSULTA = ("Consulta", "Control", "Urgencia")
PRIORIDADES = ("Normal", "Urgente")


class GestorAtencion(Gestor):
    def reservar_turno(self, mascota_id, veterinario_id, inicio, fin):
        """La superposición de turnos la impide un trigger de la base."""
        with self._transaccion() as conexion:
            validar_fecha_hora(inicio, "Inicio")
            validar_fecha_hora(fin, "Fin")
            if inicio >= fin:
                raise ErrorNegocio("El turno debe terminar después de empezar")
            self._exigir(MascotaDAO(conexion).obtener_por_id(mascota_id), "La mascota no existe")
            self._exigir(CatalogoDAO(conexion).obtener_veterinario(veterinario_id), "El veterinario no existe")
            return TurnoDAO(conexion).crear(mascota_id, veterinario_id, inicio, fin)

    def cancelar_turno(self, id):
        with self._transaccion() as conexion:
            dao = TurnoDAO(conexion)
            turno = self._exigir(dao.obtener_por_id(id), "El turno no existe")
            if turno["estado"] != "Reservado":
                raise ErrorNegocio(f"No se puede cancelar un turno en estado {turno['estado']}")
            dao.cambiar_estado(id, "Cancelado")

    def listar_turnos(self, veterinario_id):
        with self._transaccion() as conexion:
            return TurnoDAO(conexion).listar_por_veterinario(veterinario_id)

    def listar_turnos_reservados(self, mascota_id):
        with self._transaccion() as conexion:
            return TurnoDAO(conexion).listar_reservados_por_mascota(mascota_id)

    def listar_consultas(self):
        with self._transaccion() as conexion:
            return ConsultaDAO(conexion).listar_detallado()

    def registrar_consulta(self, mascota_id, veterinario_id, fecha_hora, tipo, precio, motivo=None,
                           diagnostico=None, tratamiento=None, turno_id=None, vacunas=()):
        """Registra la atención y las vacunas aplicadas, e informa cómo queda el esquema.

        vacunas es una lista de pares (vacuna_id, lote). El turno es opcional, para las urgencias.
        """
        with self._transaccion() as conexion:
            validar_fecha_hora(fecha_hora, "Fecha de la consulta")
            if tipo not in TIPOS_CONSULTA:
                raise ErrorNegocio(f"Tipo de consulta inválido: {tipo}")
            if precio < 0:
                raise ErrorNegocio("El precio no puede ser negativo")
            mascota_dao = MascotaDAO(conexion)
            mascota = self._exigir(mascota_dao.obtener_por_id(mascota_id), "La mascota no existe")
            historia = mascota_dao.obtener_historia(mascota_id)
            veterinario = self._exigir(
                CatalogoDAO(conexion).obtener_veterinario(veterinario_id), "El veterinario no existe"
            )
            if turno_id is not None:
                self._atender_turno(conexion, turno_id, mascota_id)
            consulta_id = ConsultaDAO(conexion).crear(
                historia["id"], veterinario_id, veterinario["clinica_id"], turno_id, fecha_hora, tipo,
                motivo, diagnostico, tratamiento, precio,
            )
            for vacuna_id, lote in vacunas:
                self._aplicar_vacuna(conexion, consulta_id, mascota, vacuna_id, lote, fecha_hora)
            esquema = self._calcular_esquema(conexion, mascota, historia["id"], fecha_hora)
            return {"consulta_id": consulta_id, **esquema}

    def esquema_vacunas(self, mascota_id, fecha_hora):
        """Compara las vacunas obligatorias de la especie con las aplicadas a la mascota."""
        with self._transaccion() as conexion:
            validar_fecha_hora(fecha_hora, "Fecha")
            mascota_dao = MascotaDAO(conexion)
            mascota = self._exigir(mascota_dao.obtener_por_id(mascota_id), "La mascota no existe")
            return self._calcular_esquema(conexion, mascota, mascota_dao.obtener_historia(mascota_id)["id"], fecha_hora)

    def emitir_orden(self, consulta_id, laboratorio_id, fecha_emision, muestras, responsable,
                     prioridad="Normal", observaciones=None):
        """Emite la orden con una o más muestras, que nacen en estado Extraída.

        muestras es una lista de pares (tipo_analisis_id, fecha_extraccion).
        """
        with self._transaccion() as conexion:
            validar_fecha_hora(fecha_emision, "Fecha de emisión")
            validar_obligatorio(responsable, "Responsable")
            if prioridad not in PRIORIDADES:
                raise ErrorNegocio(f"Prioridad inválida: {prioridad}")
            if not muestras:
                raise ErrorNegocio("La orden debe incluir al menos una muestra")
            self._exigir(ConsultaDAO(conexion).obtener_por_id(consulta_id), "La consulta no existe")
            catalogo = CatalogoDAO(conexion)
            self._exigir(catalogo.obtener_laboratorio(laboratorio_id), "El laboratorio no existe")
            orden_id = OrdenDAO(conexion).crear(consulta_id, laboratorio_id, fecha_emision, prioridad, observaciones)
            muestra_dao = MuestraDAO(conexion)
            codigos = []
            for tipo_analisis_id, fecha_extraccion in muestras:
                validar_fecha_hora(fecha_extraccion, "Fecha de extracción")
                self._exigir(catalogo.obtener_tipo_analisis(tipo_analisis_id), "El tipo de análisis no existe")
                muestra = Muestra(muestra_dao.siguiente_codigo(), orden_id, tipo_analisis_id,
                                  fecha_extraccion, responsable)
                muestra_dao.crear(muestra)
                codigos.append(muestra.codigo)
            return {"orden_id": orden_id, "codigos": codigos}

    def _atender_turno(self, conexion, turno_id, mascota_id):
        dao = TurnoDAO(conexion)
        turno = self._exigir(dao.obtener_por_id(turno_id), "El turno no existe")
        if turno["mascota_id"] != mascota_id:
            raise ErrorNegocio("El turno corresponde a otra mascota")
        if turno["estado"] != "Reservado":
            raise ErrorNegocio(f"No se puede atender un turno en estado {turno['estado']}")
        dao.cambiar_estado(turno_id, "Atendido")

    def _aplicar_vacuna(self, conexion, consulta_id, mascota, vacuna_id, lote, fecha_hora):
        dao = VacunaDAO(conexion)
        vacuna = self._exigir(dao.obtener_por_id(vacuna_id), "La vacuna no existe")
        if vacuna["especie_id"] != mascota.especie_id:
            raise ErrorNegocio(f"La vacuna {vacuna['nombre']} no corresponde a la especie de la mascota")
        dao.registrar_aplicacion(consulta_id, vacuna_id, lote, fecha_hora,
                                 self._calcular_proxima_dosis(fecha_hora, vacuna["intervalo_dias"]))

    def _calcular_proxima_dosis(self, fecha_hora, intervalo_dias):
        if intervalo_dias is None:
            return None
        fecha = datetime.strptime(fecha_hora, FORMATO_FECHA_HORA) + timedelta(days=intervalo_dias)
        return fecha.strftime(FORMATO_FECHA_HORA)

    def _calcular_esquema(self, conexion, mascota, historia_id, fecha_hora):
        pendientes = []
        vencidas = []
        for vacuna in VacunaDAO(conexion).listar_obligatorias_con_ultima_aplicacion(mascota.especie_id, historia_id):
            if vacuna["aplicaciones"] == 0:
                pendientes.append(vacuna["nombre"])
            elif vacuna["fecha_proxima"] and vacuna["fecha_proxima"] < fecha_hora:
                vencidas.append(vacuna["nombre"])
        return {"vacunas_pendientes": pendientes, "vacunas_vencidas": vencidas}
