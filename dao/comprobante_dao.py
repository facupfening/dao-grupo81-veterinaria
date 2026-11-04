from dao.base_dao import BaseDAO


class ComprobanteDAO(BaseDAO):
    def siguiente_numero(self):
        return self._siguiente_codigo("comprobantes", "C")

    def crear(self, numero, cliente_id, clinica_id, fecha, total):
        cursor = self._conexion.execute(
            "INSERT INTO comprobantes (numero, cliente_id, clinica_id, fecha, total) VALUES (?, ?, ?, ?, ?)",
            (numero, cliente_id, clinica_id, fecha, total),
        )
        return cursor.lastrowid

    def agregar_detalle(self, comprobante_id, consulta_id, muestra_id, descripcion, cantidad, precio_unitario):
        self._conexion.execute(
            """INSERT INTO detalles_comprobante (comprobante_id, consulta_id, muestra_id, descripcion,
                                                 cantidad, precio_unitario)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (comprobante_id, consulta_id, muestra_id, descripcion, cantidad, precio_unitario),
        )

    def obtener_por_id(self, id):
        return self._conexion.execute("SELECT * FROM comprobantes WHERE id = ?", (id,)).fetchone()

    def listar_detalles(self, comprobante_id):
        return self._conexion.execute(
            "SELECT * FROM detalles_comprobante WHERE comprobante_id = ? ORDER BY id", (comprobante_id,)
        ).fetchall()

    def consulta_facturada(self, consulta_id):
        fila = self._conexion.execute(
            "SELECT EXISTS (SELECT 1 FROM detalles_comprobante WHERE consulta_id = ?)", (consulta_id,)
        ).fetchone()
        return bool(fila[0])

    def listar_analisis_a_facturar(self, consulta_id):
        """Muestras analizadas de la consulta que todavía no se facturaron."""
        return self._conexion.execute(
            """SELECT m.id, m.codigo, t.nombre AS analisis, t.precio
               FROM muestras m
               JOIN tipos_analisis t ON t.id = m.tipo_analisis_id
               JOIN ordenes_derivacion o ON o.id = m.orden_id
               WHERE o.consulta_id = ?
                 AND m.estado_actual = 'Analizada'
                 AND NOT EXISTS (SELECT 1 FROM detalles_comprobante d WHERE d.muestra_id = m.id)
               ORDER BY m.id""",
            (consulta_id,),
        ).fetchall()
