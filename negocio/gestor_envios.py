from dao.catalogo_dao import CatalogoDAO
from dao.conservadora_dao import ConservadoraDAO
from dao.muestra_dao import MuestraDAO
from dao.remito_dao import RemitoDAO
from modelos.remito import Remito
from modelos.validaciones import validar_fecha_hora, validar_obligatorio
from negocio.gestor import ErrorNegocio, Gestor

DESPACHO = "Despacho"
TRASPASO = "Traspaso"
ARRIBO = "Arribo"


class GestorEnvios(Gestor):
    def listar_muestras_para_empaquetar(self):
        with self._transaccion() as conexion:
            return MuestraDAO(conexion).listar_para_empaquetar()

    def listar_conservadoras_disponibles(self):
        with self._transaccion() as conexion:
            return ConservadoraDAO(conexion).listar_disponibles()

    def empaquetar(self, muestra_ids, conservadora_id, fecha_hora, responsable):
        """Genera el remito y el precinto, y empaqueta las muestras en la conservadora."""
        with self._transaccion() as conexion:
            validar_fecha_hora(fecha_hora, "Fecha de empaquetado")
            validar_obligatorio(responsable, "Responsable")
            if not muestra_ids:
                raise ErrorNegocio("Debe seleccionar al menos una muestra")
            if len(set(muestra_ids)) != len(muestra_ids):
                raise ErrorNegocio("Hay muestras repetidas en la selección")

            conservadora_dao = ConservadoraDAO(conexion)
            conservadora = self._exigir(conservadora_dao.obtener_por_id(conservadora_id), "La conservadora no existe")
            if conservadora["estado"] != "Disponible":
                raise ErrorNegocio(f"La conservadora {conservadora['codigo']} no está disponible")
            if len(muestra_ids) > conservadora["capacidad"]:
                raise ErrorNegocio(f"La conservadora {conservadora['codigo']} admite {conservadora['capacidad']} muestras")

            muestra_dao = MuestraDAO(conexion)
            muestras = []
            destinos = set()
            for muestra_id in muestra_ids:
                muestra = self._exigir(muestra_dao.obtener_por_id(muestra_id), f"La muestra {muestra_id} no existe")
                datos = muestra_dao.obtener_datos_empaquetado(muestra_id)
                # La temperatura de la conservadora debe quedar dentro del rango que tolera la muestra.
                if conservadora["temp_min"] < datos["temp_min"] or conservadora["temp_max"] > datos["temp_max"]:
                    raise ErrorNegocio(
                        f"La muestra {muestra.codigo} requiere entre {datos['temp_min']} y {datos['temp_max']} °C: "
                        f"la conservadora {conservadora['codigo']} no es compatible"
                    )
                destinos.add((datos["clinica_id"], datos["laboratorio_id"]))
                muestras.append(muestra)
            if len(destinos) > 1:
                raise ErrorNegocio("Las muestras de un remito deben tener la misma clínica y el mismo laboratorio")
            clinica_id, laboratorio_id = destinos.pop()

            remito_dao = RemitoDAO(conexion)
            remito = Remito(remito_dao.siguiente_numero(), clinica_id, laboratorio_id, conservadora_id,
                            fecha_hora, responsable)
            for muestra in muestras:
                remito.agregar_muestra(muestra, fecha_hora, responsable)
            remito_dao.crear(remito)
            for muestra in remito.muestras:
                muestra_dao.asignar_remito(muestra.id, remito.id)
                muestra_dao.guardar_estado(muestra)
            precinto = remito_dao.crear_precinto(remito.id, fecha_hora, responsable)
            conservadora_dao.cambiar_estado(conservadora_id, "En uso")
            return {"remito_id": remito.id, "numero": remito.numero, "precinto": precinto}

    def registrar_evento(self, remito_id, transportista_id, tipo, fecha_hora, ubicacion, temperatura, responsable):
        """Un despacho pasa el remito a Despachado; el traspaso o arribo siguiente, a En tránsito."""
        with self._transaccion() as conexion:
            validar_fecha_hora(fecha_hora, "Fecha del evento")
            validar_obligatorio(ubicacion, "Ubicación")
            validar_obligatorio(responsable, "Responsable")
            if tipo not in (DESPACHO, TRASPASO, ARRIBO):
                raise ErrorNegocio(f"Tipo de evento inválido: {tipo}")
            if temperatura is None:
                raise ErrorNegocio("La temperatura es obligatoria")
            self._exigir(CatalogoDAO(conexion).obtener_transportista(transportista_id), "El transportista no existe")
            remito_dao = RemitoDAO(conexion)
            remito = self._exigir(remito_dao.obtener_por_id(remito_id), "El remito no existe")
            if tipo == DESPACHO:
                remito.despachar(fecha_hora, responsable)
            else:
                remito.registrar_tramo(fecha_hora, responsable, tipo)
            evento_id = remito_dao.crear_evento(remito_id, transportista_id, tipo, fecha_hora, ubicacion,
                                                temperatura, responsable)
            self._guardar_remito_y_muestras(conexion, remito)
            return evento_id

    def registrar_recepcion(self, remito_id, estado_precinto, fecha_hora, recibido_por, temp_llegada,
                            observaciones=None):
        """Con el precinto roto se rechazan el remito y todas sus muestras. La conservadora queda libre."""
        with self._transaccion() as conexion:
            validar_fecha_hora(fecha_hora, "Fecha de recepción")
            validar_obligatorio(recibido_por, "Recibido por")
            if temp_llegada is None:
                raise ErrorNegocio("La temperatura de llegada es obligatoria")
            remito_dao = RemitoDAO(conexion)
            remito = self._exigir(remito_dao.obtener_por_id(remito_id), "El remito no existe")
            remito.registrar_recepcion(estado_precinto, fecha_hora, recibido_por, observaciones)
            remito_dao.crear_recepcion(remito_id, fecha_hora, recibido_por, estado_precinto, temp_llegada, observaciones)
            self._guardar_remito_y_muestras(conexion, remito)
            ConservadoraDAO(conexion).cambiar_estado(remito.conservadora_id, "Disponible")
            return remito.estado

    def obtener_remito(self, remito_id):
        with self._transaccion() as conexion:
            return RemitoDAO(conexion).obtener_por_id(remito_id)

    def listar_remitos(self):
        with self._transaccion() as conexion:
            return RemitoDAO(conexion).listar()

    def obtener_trazabilidad(self, remito_id):
        """Reúne el remito con sus muestras, el precinto, los eventos de envío y la recepción."""
        with self._transaccion() as conexion:
            dao = RemitoDAO(conexion)
            return {
                "remito": self._exigir(dao.obtener_por_id(remito_id), "El remito no existe"),
                "precinto": dao.obtener_precinto(remito_id),
                "eventos": dao.listar_eventos(remito_id),
                "recepcion": dao.obtener_recepcion(remito_id),
            }

    def _guardar_remito_y_muestras(self, conexion, remito):
        RemitoDAO(conexion).guardar_estado(remito)
        muestra_dao = MuestraDAO(conexion)
        for muestra in remito.muestras:
            muestra_dao.guardar_estado(muestra)
