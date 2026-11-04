from dao.base_dao import BaseDAO


class ReporteDAO(BaseDAO):
    """Consultas de los reportes. Los períodos llegan como textos 'AAAA-MM-DD HH:MM'."""

    def atenciones_por_clinica(self, desde, hasta):
        return self._conexion.execute(
            """SELECT cl.nombre AS clinica,
                      COALESCE(SUM(c.tipo = 'Consulta'), 0) AS consultas,
                      COALESCE(SUM(c.tipo = 'Control'), 0) AS controles,
                      COALESCE(SUM(c.tipo = 'Urgencia'), 0) AS urgencias,
                      COUNT(c.id) AS total,
                      (SELECT COUNT(*) FROM ordenes_derivacion o
                       JOIN consultas co ON co.id = o.consulta_id
                       WHERE co.clinica_id = cl.id AND o.fecha_emision BETWEEN :desde AND :hasta) AS ordenes
               FROM clinicas cl
               LEFT JOIN consultas c ON c.clinica_id = cl.id AND c.fecha_hora BETWEEN :desde AND :hasta
               GROUP BY cl.id
               ORDER BY cl.nombre""",
            {"desde": desde, "hasta": hasta},
        ).fetchall()

    def muestras_rechazadas(self, desde, hasta):
        """El transportista informado es el del último evento: quien entregó el remito."""
        return self._conexion.execute(
            """SELECT cl.nombre AS clinica, t.nombre AS transportista, r.numero AS remito,
                      p.numero AS precinto, m.codigo AS muestra, ta.nombre AS analisis,
                      rc.fecha_hora AS fecha
               FROM muestras m
               JOIN remitos_biologicos r ON r.id = m.remito_id
               JOIN clinicas cl ON cl.id = r.clinica_id
               JOIN precintos p ON p.remito_id = r.id
               JOIN recepciones rc ON rc.remito_id = r.id
               JOIN tipos_analisis ta ON ta.id = m.tipo_analisis_id
               JOIN eventos_envio e ON e.id = (SELECT e2.id FROM eventos_envio e2
                                               WHERE e2.remito_id = r.id
                                               ORDER BY e2.fecha_hora DESC, e2.id DESC LIMIT 1)
               JOIN transportistas t ON t.id = e.transportista_id
               WHERE m.estado_actual = 'Rechazada' AND rc.fecha_hora BETWEEN :desde AND :hasta
               ORDER BY cl.nombre, t.nombre, r.numero, m.codigo""",
            {"desde": desde, "hasta": hasta},
        ).fetchall()

    def tratamientos(self, desde, hasta):
        return self._conexion.execute(
            """SELECT c.fecha_hora, cl.nombre AS clinica, m.nombre AS mascota,
                      v.apellido || ', ' || v.nombre AS veterinario, c.diagnostico, c.tratamiento
               FROM consultas c
               JOIN clinicas cl ON cl.id = c.clinica_id
               JOIN veterinarios v ON v.id = c.veterinario_id
               JOIN historias_clinicas h ON h.id = c.historia_id
               JOIN mascotas m ON m.id = h.mascota_id
               WHERE c.tratamiento IS NOT NULL AND TRIM(c.tratamiento) <> ''
                 AND c.fecha_hora BETWEEN :desde AND :hasta
               ORDER BY c.fecha_hora""",
            {"desde": desde, "hasta": hasta},
        ).fetchall()

    def facturacion(self, desde, hasta):
        return self._conexion.execute(
            """SELECT cl.nombre AS clinica,
                      d.muestra_id IS NOT NULL AS es_laboratorio,
                      COALESCE(t.nombre, 'Consultas') AS concepto,
                      SUM(d.cantidad) AS cantidad,
                      SUM(d.cantidad * d.precio_unitario) AS importe
               FROM detalles_comprobante d
               JOIN comprobantes co ON co.id = d.comprobante_id
               JOIN clinicas cl ON cl.id = co.clinica_id
               LEFT JOIN muestras m ON m.id = d.muestra_id
               LEFT JOIN tipos_analisis t ON t.id = m.tipo_analisis_id
               WHERE co.fecha BETWEEN :desde AND :hasta
               GROUP BY cl.id, concepto
               ORDER BY cl.nombre, es_laboratorio, concepto""",
            {"desde": desde, "hasta": hasta},
        ).fetchall()

    def tiempos_de_transito(self, desde, hasta):
        """Horas desde el despacho hasta la recepción, sea aceptada o rechazada."""
        return self._conexion.execute(
            """SELECT cl.nombre AS clinica, COUNT(*) AS cantidad,
                      AVG((julianday(fin.fecha_hora) - julianday(ini.fecha_hora)) * 24) AS horas
               FROM remitos_biologicos r
               JOIN clinicas cl ON cl.id = r.clinica_id
               JOIN historial_estados_remito ini ON ini.remito_id = r.id AND ini.estado = 'Despachado'
               JOIN historial_estados_remito fin ON fin.remito_id = r.id AND fin.estado IN ('Recibido', 'Rechazado')
               WHERE fin.fecha_hora BETWEEN :desde AND :hasta
               GROUP BY cl.id
               ORDER BY cl.nombre""",
            {"desde": desde, "hasta": hasta},
        ).fetchall()

    def tiempos_de_procesamiento(self, desde, hasta):
        """Horas desde la recepción hasta el resultado de cada muestra analizada."""
        return self._conexion.execute(
            """SELECT t.nombre AS analisis, COUNT(*) AS cantidad,
                      AVG((julianday(fin.fecha_hora) - julianday(ini.fecha_hora)) * 24) AS horas
               FROM muestras m
               JOIN tipos_analisis t ON t.id = m.tipo_analisis_id
               JOIN historial_estados_muestra ini ON ini.muestra_id = m.id AND ini.estado = 'Recibida'
               JOIN historial_estados_muestra fin ON fin.muestra_id = m.id AND fin.estado = 'Analizada'
               WHERE fin.fecha_hora BETWEEN :desde AND :hasta
               GROUP BY t.id
               ORDER BY t.nombre""",
            {"desde": desde, "hasta": hasta},
        ).fetchall()
