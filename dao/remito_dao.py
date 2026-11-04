from dao.base_dao import BaseDAO
from dao.muestra_dao import MuestraDAO
from modelos.remito import Remito

TABLA_HISTORIAL = "historial_estados_remito"


class RemitoDAO(BaseDAO):
    def siguiente_numero(self):
        return self._siguiente_codigo("remitos_biologicos", "R")

    def crear(self, remito):
        cursor = self._conexion.execute(
            """INSERT INTO remitos_biologicos (numero, clinica_id, laboratorio_id, conservadora_id,
                                               fecha_emision, estado_actual)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (remito.numero, remito.clinica_id, remito.laboratorio_id, remito.conservadora_id,
             remito.fecha_emision, remito.estado),
        )
        remito.id = cursor.lastrowid
        self._guardar_historial(TABLA_HISTORIAL, "remito_id", remito.id, remito.historial)
        return remito.id

    def obtener_por_id(self, id):
        fila = self._conexion.execute("SELECT * FROM remitos_biologicos WHERE id = ?", (id,)).fetchone()
        return self._a_remito(fila) if fila else None

    def listar(self):
        filas = self._conexion.execute("SELECT * FROM remitos_biologicos ORDER BY id DESC").fetchall()
        return [self._a_remito(fila) for fila in filas]

    def guardar_estado(self, remito):
        self._conexion.execute(
            "UPDATE remitos_biologicos SET estado_actual = ? WHERE id = ?", (remito.estado, remito.id)
        )
        self._guardar_historial(TABLA_HISTORIAL, "remito_id", remito.id, remito.historial)

    def crear_precinto(self, remito_id, fecha_colocacion, colocado_por):
        numero = self._siguiente_codigo("precintos", "P")
        self._conexion.execute(
            "INSERT INTO precintos (remito_id, numero, fecha_colocacion, colocado_por) VALUES (?, ?, ?, ?)",
            (remito_id, numero, fecha_colocacion, colocado_por),
        )
        return numero

    def obtener_precinto(self, remito_id):
        return self._conexion.execute("SELECT * FROM precintos WHERE remito_id = ?", (remito_id,)).fetchone()

    def crear_evento(self, remito_id, transportista_id, tipo, fecha_hora, ubicacion, temperatura, responsable):
        cursor = self._conexion.execute(
            """INSERT INTO eventos_envio (remito_id, transportista_id, tipo, fecha_hora, ubicacion,
                                          temperatura, responsable)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (remito_id, transportista_id, tipo, fecha_hora, ubicacion, temperatura, responsable),
        )
        return cursor.lastrowid

    def listar_eventos(self, remito_id):
        return self._conexion.execute(
            "SELECT * FROM eventos_envio WHERE remito_id = ? ORDER BY fecha_hora, id", (remito_id,)
        ).fetchall()

    def crear_recepcion(self, remito_id, fecha_hora, recibido_por, estado_precinto, temp_llegada, observaciones):
        cursor = self._conexion.execute(
            """INSERT INTO recepciones (remito_id, fecha_hora, recibido_por, estado_precinto, temp_llegada, observaciones)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (remito_id, fecha_hora, recibido_por, estado_precinto, temp_llegada, observaciones),
        )
        return cursor.lastrowid

    def obtener_recepcion(self, remito_id):
        return self._conexion.execute("SELECT * FROM recepciones WHERE remito_id = ?", (remito_id,)).fetchone()

    def _a_remito(self, fila):
        historial = self._leer_historial(TABLA_HISTORIAL, "remito_id", fila["id"])
        muestras = MuestraDAO(self._conexion).listar_por_remito(fila["id"])
        return Remito(fila["numero"], fila["clinica_id"], fila["laboratorio_id"], fila["conservadora_id"],
                      fila["fecha_emision"], estado=fila["estado_actual"], historial=historial,
                      muestras=muestras, id=fila["id"])
