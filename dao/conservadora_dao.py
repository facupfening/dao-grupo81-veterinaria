from dao.base_dao import BaseDAO


class ConservadoraDAO(BaseDAO):
    def obtener_por_id(self, id):
        return self._conexion.execute("SELECT * FROM conservadoras WHERE id = ?", (id,)).fetchone()

    def listar_disponibles(self):
        return self._conexion.execute(
            "SELECT * FROM conservadoras WHERE estado = 'Disponible' ORDER BY codigo"
        ).fetchall()

    def cambiar_estado(self, id, estado):
        self._conexion.execute("UPDATE conservadoras SET estado = ? WHERE id = ?", (estado, id))
