from dao.base_dao import BaseDAO
from modelos.cliente import Cliente


class ClienteDAO(BaseDAO):
    def crear(self, cliente):
        cursor = self._conexion.execute(
            "INSERT INTO clientes (dni, nombre, apellido, telefono, email, direccion) VALUES (?, ?, ?, ?, ?, ?)",
            (cliente.dni, cliente.nombre, cliente.apellido, cliente.telefono, cliente.email, cliente.direccion),
        )
        cliente.id = cursor.lastrowid
        return cliente.id

    def obtener_por_id(self, id):
        fila = self._conexion.execute("SELECT * FROM clientes WHERE id = ?", (id,)).fetchone()
        return self._a_cliente(fila) if fila else None

    def obtener_por_dni(self, dni):
        fila = self._conexion.execute("SELECT * FROM clientes WHERE dni = ?", (dni,)).fetchone()
        return self._a_cliente(fila) if fila else None

    def listar(self):
        filas = self._conexion.execute("SELECT * FROM clientes ORDER BY apellido, nombre").fetchall()
        return [self._a_cliente(fila) for fila in filas]

    def buscar_por_apellido(self, apellido):
        filas = self._conexion.execute(
            "SELECT * FROM clientes WHERE apellido LIKE ? ORDER BY apellido, nombre", (f"%{apellido}%",)
        ).fetchall()
        return [self._a_cliente(fila) for fila in filas]

    def actualizar(self, cliente):
        cursor = self._conexion.execute(
            """UPDATE clientes SET dni = ?, nombre = ?, apellido = ?, telefono = ?, email = ?, direccion = ?
               WHERE id = ?""",
            (cliente.dni, cliente.nombre, cliente.apellido, cliente.telefono, cliente.email,
             cliente.direccion, cliente.id),
        )
        return cursor.rowcount > 0

    def eliminar(self, id):
        cursor = self._conexion.execute("DELETE FROM clientes WHERE id = ?", (id,))
        return cursor.rowcount > 0

    def _a_cliente(self, fila):
        return Cliente(fila["dni"], fila["nombre"], fila["apellido"], fila["telefono"], fila["email"],
                       fila["direccion"], fila["id"])
