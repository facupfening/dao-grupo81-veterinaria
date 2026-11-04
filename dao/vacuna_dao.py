from dao.base_dao import BaseDAO


class VacunaDAO(BaseDAO):
    def obtener_por_id(self, id):
        return self._conexion.execute("SELECT * FROM vacunas WHERE id = ?", (id,)).fetchone()

    def listar_por_especie(self, especie_id):
        return self._conexion.execute(
            "SELECT * FROM vacunas WHERE especie_id = ? ORDER BY nombre", (especie_id,)
        ).fetchall()

    def registrar_aplicacion(self, consulta_id, vacuna_id, lote, fecha_aplicacion, fecha_proxima):
        cursor = self._conexion.execute(
            """INSERT INTO aplicaciones_vacuna (consulta_id, vacuna_id, lote, fecha_aplicacion, fecha_proxima)
               VALUES (?, ?, ?, ?, ?)""",
            (consulta_id, vacuna_id, lote, fecha_aplicacion, fecha_proxima),
        )
        return cursor.lastrowid

    def listar_aplicaciones_por_historia(self, historia_id):
        return self._conexion.execute(
            """SELECT a.*, v.nombre AS vacuna FROM aplicaciones_vacuna a
               JOIN vacunas v ON v.id = a.vacuna_id
               JOIN consultas c ON c.id = a.consulta_id
               WHERE c.historia_id = ?
               ORDER BY a.fecha_aplicacion""",
            (historia_id,),
        ).fetchall()

    def listar_obligatorias_con_ultima_aplicacion(self, especie_id, historia_id):
        """Una fila por vacuna obligatoria con la última aplicación que recibió esa mascota."""
        return self._conexion.execute(
            """SELECT v.id, v.nombre,
                      (SELECT a.fecha_proxima FROM aplicaciones_vacuna a
                       JOIN consultas c ON c.id = a.consulta_id
                       WHERE a.vacuna_id = v.id AND c.historia_id = ?
                       ORDER BY a.fecha_aplicacion DESC, a.id DESC LIMIT 1) AS fecha_proxima,
                      (SELECT COUNT(*) FROM aplicaciones_vacuna a
                       JOIN consultas c ON c.id = a.consulta_id
                       WHERE a.vacuna_id = v.id AND c.historia_id = ?) AS aplicaciones
               FROM vacunas v
               WHERE v.especie_id = ? AND v.obligatoria = 1
               ORDER BY v.nombre""",
            (historia_id, historia_id, especie_id),
        ).fetchall()
