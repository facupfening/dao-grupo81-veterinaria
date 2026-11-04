from dao.base_dao import BaseDAO


class OrdenDAO(BaseDAO):
    def crear(self, consulta_id, laboratorio_id, fecha_emision, prioridad, observaciones):
        cursor = self._conexion.execute(
            """INSERT INTO ordenes_derivacion (consulta_id, laboratorio_id, fecha_emision, prioridad, observaciones)
               VALUES (?, ?, ?, ?, ?)""",
            (consulta_id, laboratorio_id, fecha_emision, prioridad, observaciones),
        )
        return cursor.lastrowid

    def obtener_por_id(self, id):
        return self._conexion.execute("SELECT * FROM ordenes_derivacion WHERE id = ?", (id,)).fetchone()

    def listar_por_historia(self, historia_id):
        return self._conexion.execute(
            """SELECT o.* FROM ordenes_derivacion o
               JOIN consultas c ON c.id = o.consulta_id
               WHERE c.historia_id = ?
               ORDER BY o.fecha_emision""",
            (historia_id,),
        ).fetchall()
