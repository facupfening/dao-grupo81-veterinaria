from dao.base_dao import BaseDAO
from modelos.mascota import Mascota


class MascotaDAO(BaseDAO):
    def crear(self, mascota):
        cursor = self._conexion.execute(
            """INSERT INTO mascotas (cliente_id, especie_id, nombre, raza, sexo, fecha_nacimiento, peso_kg)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (mascota.cliente_id, mascota.especie_id, mascota.nombre, mascota.raza, mascota.sexo,
             mascota.fecha_nacimiento, mascota.peso_kg),
        )
        mascota.id = cursor.lastrowid
        return mascota.id

    def obtener_por_id(self, id):
        fila = self._conexion.execute("SELECT * FROM mascotas WHERE id = ?", (id,)).fetchone()
        return self._a_mascota(fila) if fila else None

    def listar(self):
        filas = self._conexion.execute("SELECT * FROM mascotas ORDER BY nombre").fetchall()
        return [self._a_mascota(fila) for fila in filas]

    def listar_detallado(self):
        """Mascotas con el nombre de su responsable y de su especie, listas para mostrar."""
        return self._conexion.execute(
            """SELECT m.*, e.nombre AS especie, c.apellido || ', ' || c.nombre AS responsable
               FROM mascotas m
               JOIN especies e ON e.id = m.especie_id
               JOIN clientes c ON c.id = m.cliente_id
               ORDER BY m.nombre"""
        ).fetchall()

    def listar_por_cliente(self, cliente_id):
        filas = self._conexion.execute(
            "SELECT * FROM mascotas WHERE cliente_id = ? ORDER BY nombre", (cliente_id,)
        ).fetchall()
        return [self._a_mascota(fila) for fila in filas]

    def actualizar(self, mascota):
        cursor = self._conexion.execute(
            """UPDATE mascotas SET cliente_id = ?, especie_id = ?, nombre = ?, raza = ?, sexo = ?,
               fecha_nacimiento = ?, peso_kg = ? WHERE id = ?""",
            (mascota.cliente_id, mascota.especie_id, mascota.nombre, mascota.raza, mascota.sexo,
             mascota.fecha_nacimiento, mascota.peso_kg, mascota.id),
        )
        return cursor.rowcount > 0

    def eliminar(self, id):
        cursor = self._conexion.execute("DELETE FROM mascotas WHERE id = ?", (id,))
        return cursor.rowcount > 0

    def tiene_atenciones(self, id):
        fila = self._conexion.execute(
            """SELECT EXISTS (SELECT 1 FROM turnos WHERE mascota_id = ?)
                   OR EXISTS (SELECT 1 FROM consultas c
                              JOIN historias_clinicas h ON h.id = c.historia_id
                              WHERE h.mascota_id = ?)""",
            (id, id),
        ).fetchone()
        return bool(fila[0])

    def crear_historia(self, mascota_id, fecha_apertura, antecedentes=None):
        cursor = self._conexion.execute(
            "INSERT INTO historias_clinicas (mascota_id, fecha_apertura, antecedentes) VALUES (?, ?, ?)",
            (mascota_id, fecha_apertura, antecedentes),
        )
        return cursor.lastrowid

    def obtener_historia(self, mascota_id):
        return self._conexion.execute(
            "SELECT * FROM historias_clinicas WHERE mascota_id = ?", (mascota_id,)
        ).fetchone()

    def actualizar_antecedentes(self, mascota_id, antecedentes):
        cursor = self._conexion.execute(
            "UPDATE historias_clinicas SET antecedentes = ? WHERE mascota_id = ?", (antecedentes, mascota_id)
        )
        return cursor.rowcount > 0

    def eliminar_historia(self, mascota_id):
        self._conexion.execute("DELETE FROM historias_clinicas WHERE mascota_id = ?", (mascota_id,))

    def _a_mascota(self, fila):
        return Mascota(fila["cliente_id"], fila["especie_id"], fila["nombre"], fila["raza"], fila["sexo"],
                       fila["fecha_nacimiento"], fila["peso_kg"], fila["id"])
