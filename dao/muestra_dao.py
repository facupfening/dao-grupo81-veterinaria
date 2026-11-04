from dao.base_dao import BaseDAO
from modelos.muestra import Muestra

TABLA_HISTORIAL = "historial_estados_muestra"


class MuestraDAO(BaseDAO):
    def siguiente_codigo(self):
        return self._siguiente_codigo("muestras", "M")

    def crear(self, muestra):
        cursor = self._conexion.execute(
            """INSERT INTO muestras (orden_id, tipo_analisis_id, codigo, fecha_extraccion, estado_actual)
               VALUES (?, ?, ?, ?, ?)""",
            (muestra.orden_id, muestra.tipo_analisis_id, muestra.codigo, muestra.fecha_extraccion, muestra.estado),
        )
        muestra.id = cursor.lastrowid
        self._guardar_historial(TABLA_HISTORIAL, "muestra_id", muestra.id, muestra.historial)
        return muestra.id

    def obtener_por_id(self, id):
        fila = self._conexion.execute("SELECT * FROM muestras WHERE id = ?", (id,)).fetchone()
        return self._a_muestra(fila) if fila else None

    def listar_por_orden(self, orden_id):
        filas = self._conexion.execute("SELECT * FROM muestras WHERE orden_id = ? ORDER BY id", (orden_id,)).fetchall()
        return [self._a_muestra(fila) for fila in filas]

    def listar_por_remito(self, remito_id):
        filas = self._conexion.execute("SELECT * FROM muestras WHERE remito_id = ? ORDER BY id", (remito_id,)).fetchall()
        return [self._a_muestra(fila) for fila in filas]

    def listar_para_empaquetar(self):
        return self._conexion.execute(
            """SELECT m.id, m.codigo, t.nombre AS analisis, t.temp_min, t.temp_max,
                      c.clinica_id, o.laboratorio_id, o.prioridad
               FROM muestras m
               JOIN tipos_analisis t ON t.id = m.tipo_analisis_id
               JOIN ordenes_derivacion o ON o.id = m.orden_id
               JOIN consultas c ON c.id = o.consulta_id
               WHERE m.estado_actual = 'Extraída'
               ORDER BY o.prioridad DESC, m.id"""
        ).fetchall()

    def listar_recibidas(self):
        return self._conexion.execute(
            """SELECT m.id, m.codigo, t.nombre AS analisis FROM muestras m
               JOIN tipos_analisis t ON t.id = m.tipo_analisis_id
               WHERE m.estado_actual = 'Recibida'
               ORDER BY m.id"""
        ).fetchall()

    def obtener_datos_empaquetado(self, id):
        """Devuelve el rango de temperatura, el laboratorio y la clínica de origen de la muestra."""
        return self._conexion.execute(
            """SELECT t.temp_min, t.temp_max, o.laboratorio_id, c.clinica_id
               FROM muestras m
               JOIN tipos_analisis t ON t.id = m.tipo_analisis_id
               JOIN ordenes_derivacion o ON o.id = m.orden_id
               JOIN consultas c ON c.id = o.consulta_id
               WHERE m.id = ?""",
            (id,),
        ).fetchone()

    def asignar_remito(self, id, remito_id):
        self._conexion.execute("UPDATE muestras SET remito_id = ? WHERE id = ?", (remito_id, id))

    def guardar_estado(self, muestra):
        self._conexion.execute("UPDATE muestras SET estado_actual = ? WHERE id = ?", (muestra.estado, muestra.id))
        self._guardar_historial(TABLA_HISTORIAL, "muestra_id", muestra.id, muestra.historial)

    def crear_resultado(self, muestra_id, fecha_hora, profesional, valores, conclusion):
        cursor = self._conexion.execute(
            """INSERT INTO resultados (muestra_id, fecha_hora, profesional, valores, conclusion)
               VALUES (?, ?, ?, ?, ?)""",
            (muestra_id, fecha_hora, profesional, valores, conclusion),
        )
        return cursor.lastrowid

    def obtener_resultado(self, muestra_id):
        return self._conexion.execute("SELECT * FROM resultados WHERE muestra_id = ?", (muestra_id,)).fetchone()

    def _a_muestra(self, fila):
        historial = self._leer_historial(TABLA_HISTORIAL, "muestra_id", fila["id"])
        return Muestra(fila["codigo"], fila["orden_id"], fila["tipo_analisis_id"], fila["fecha_extraccion"],
                       estado=fila["estado_actual"], historial=historial, id=fila["id"])
