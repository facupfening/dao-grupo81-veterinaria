from modelos.registro_estado import RegistroEstado


class BaseDAO:
    """Cada DAO recibe la conexión, así varias operaciones comparten una misma transacción."""

    def __init__(self, conexion):
        self._conexion = conexion

    def _siguiente_codigo(self, tabla, prefijo):
        # Código correlativo de 6 dígitos a partir del próximo id: M-000001, R-000001, P-000001...
        fila = self._conexion.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {tabla}").fetchone()
        return f"{prefijo}-{fila[0]:06d}"

    def _leer_historial(self, tabla, columna, id):
        filas = self._conexion.execute(
            f"SELECT estado, fecha_hora, responsable, observacion FROM {tabla} WHERE {columna} = ? ORDER BY id",
            (id,),
        ).fetchall()
        return [RegistroEstado(f["estado"], f["fecha_hora"], f["responsable"], f["observacion"]) for f in filas]

    def _guardar_historial(self, tabla, columna, id, historial):
        """Inserta solo los registros nuevos: el historial nunca se actualiza ni se borra."""
        guardados = self._conexion.execute(f"SELECT COUNT(*) FROM {tabla} WHERE {columna} = ?", (id,)).fetchone()[0]
        # Los registros que siguen a los ya guardados son los que se agregaron en memoria.
        for registro in historial[guardados:]:
            self._conexion.execute(
                f"INSERT INTO {tabla} ({columna}, estado, fecha_hora, responsable, observacion) VALUES (?, ?, ?, ?, ?)",
                (id, registro.estado, registro.fecha_hora, registro.responsable, registro.observacion),
            )
