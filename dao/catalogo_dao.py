from dao.base_dao import BaseDAO


class CatalogoDAO(BaseDAO):
    """Consultas sobre tablas de referencia que el sistema solo necesita leer."""

    def listar_especies(self):
        return self._conexion.execute("SELECT * FROM especies ORDER BY nombre").fetchall()

    def obtener_especie(self, id):
        return self._conexion.execute("SELECT * FROM especies WHERE id = ?", (id,)).fetchone()

    def listar_clinicas(self):
        return self._conexion.execute("SELECT * FROM clinicas ORDER BY nombre").fetchall()

    def listar_veterinarios(self):
        # Incluye el nombre de la clínica a la que está asociado cada veterinario.
        return self._conexion.execute(
            """SELECT v.*, c.nombre AS clinica FROM veterinarios v
               JOIN clinicas c ON c.id = v.clinica_id
               ORDER BY v.apellido, v.nombre"""
        ).fetchall()

    def obtener_veterinario(self, id):
        return self._conexion.execute("SELECT * FROM veterinarios WHERE id = ?", (id,)).fetchone()

    def listar_laboratorios(self):
        return self._conexion.execute("SELECT * FROM laboratorios ORDER BY nombre").fetchall()

    def obtener_laboratorio(self, id):
        return self._conexion.execute("SELECT * FROM laboratorios WHERE id = ?", (id,)).fetchone()

    def listar_tipos_analisis(self):
        return self._conexion.execute("SELECT * FROM tipos_analisis ORDER BY nombre").fetchall()

    def obtener_tipo_analisis(self, id):
        return self._conexion.execute("SELECT * FROM tipos_analisis WHERE id = ?", (id,)).fetchone()

    def listar_transportistas(self):
        return self._conexion.execute("SELECT * FROM transportistas ORDER BY nombre").fetchall()

    def obtener_transportista(self, id):
        return self._conexion.execute("SELECT * FROM transportistas WHERE id = ?", (id,)).fetchone()
