from dao.base_dao import BaseDAO


class ConsultaDAO(BaseDAO):
    def crear(self, historia_id, veterinario_id, clinica_id, turno_id, fecha_hora, tipo, motivo,
              diagnostico, tratamiento, precio):
        cursor = self._conexion.execute(
            """INSERT INTO consultas (historia_id, veterinario_id, clinica_id, turno_id, fecha_hora, tipo,
                                      motivo, diagnostico, tratamiento, precio)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (historia_id, veterinario_id, clinica_id, turno_id, fecha_hora, tipo, motivo, diagnostico,
             tratamiento, precio),
        )
        return cursor.lastrowid

    def obtener_por_id(self, id):
        return self._conexion.execute("SELECT * FROM consultas WHERE id = ?", (id,)).fetchone()

    def listar_por_historia(self, historia_id):
        return self._conexion.execute(
            "SELECT * FROM consultas WHERE historia_id = ? ORDER BY fecha_hora", (historia_id,)
        ).fetchall()

    def listar_detallado(self):
        """Consultas con el nombre de la mascota y de la clínica, listas para mostrarlas en pantalla."""
        return self._conexion.execute(
            """SELECT c.*, m.nombre AS mascota, cl.nombre AS clinica FROM consultas c
               JOIN historias_clinicas h ON h.id = c.historia_id
               JOIN mascotas m ON m.id = h.mascota_id
               JOIN clinicas cl ON cl.id = c.clinica_id
               ORDER BY c.fecha_hora DESC, c.id DESC"""
        ).fetchall()

    def obtener_cliente_id(self, id):
        fila = self._conexion.execute(
            """SELECT m.cliente_id FROM consultas c
               JOIN historias_clinicas h ON h.id = c.historia_id
               JOIN mascotas m ON m.id = h.mascota_id
               WHERE c.id = ?""",
            (id,),
        ).fetchone()
        return fila["cliente_id"] if fila else None
