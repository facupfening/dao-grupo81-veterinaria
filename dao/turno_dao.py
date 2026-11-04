from dao.base_dao import BaseDAO


class TurnoDAO(BaseDAO):
    def crear(self, mascota_id, veterinario_id, inicio, fin):
        cursor = self._conexion.execute(
            "INSERT INTO turnos (mascota_id, veterinario_id, inicio, fin) VALUES (?, ?, ?, ?)",
            (mascota_id, veterinario_id, inicio, fin),
        )
        return cursor.lastrowid

    def obtener_por_id(self, id):
        return self._conexion.execute("SELECT * FROM turnos WHERE id = ?", (id,)).fetchone()

    def listar_por_veterinario(self, veterinario_id):
        return self._conexion.execute(
            """SELECT t.*, m.nombre AS mascota FROM turnos t
               JOIN mascotas m ON m.id = t.mascota_id
               WHERE t.veterinario_id = ?
               ORDER BY t.inicio""",
            (veterinario_id,),
        ).fetchall()

    def listar_reservados_por_mascota(self, mascota_id):
        return self._conexion.execute(
            """SELECT * FROM turnos WHERE mascota_id = ? AND estado = 'Reservado' ORDER BY inicio""",
            (mascota_id,),
        ).fetchall()

    def cambiar_estado(self, id, estado):
        self._conexion.execute("UPDATE turnos SET estado = ? WHERE id = ?", (estado, id))
