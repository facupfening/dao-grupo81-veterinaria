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
        return self._conexion.execute("SELECT * FROM veterinarios ORDER BY apellido, nombre").fetchall()

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
