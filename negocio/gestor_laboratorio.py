from dao.comprobante_dao import ComprobanteDAO
from dao.consulta_dao import ConsultaDAO
from dao.muestra_dao import MuestraDAO
from modelos.validaciones import validar_fecha_hora, validar_obligatorio
from negocio.gestor import ErrorNegocio, Gestor


class GestorLaboratorio(Gestor):
    def listar_muestras_recibidas(self):
        with self._transaccion() as conexion:
            return MuestraDAO(conexion).listar_recibidas()

    def registrar_resultado(self, muestra_id, fecha_hora, profesional, valores, conclusion=None):
        """El estado de la muestra impide cargar resultados si no fue recibida o si fue rechazada."""
        with self._transaccion() as conexion:
            validar_fecha_hora(fecha_hora, "Fecha del resultado")
            validar_obligatorio(profesional, "Profesional")
            validar_obligatorio(valores, "Valores")
            dao = MuestraDAO(conexion)
            muestra = self._exigir(dao.obtener_por_id(muestra_id), "La muestra no existe")
            muestra.analizar(fecha_hora, profesional)
            resultado_id = dao.crear_resultado(muestra_id, fecha_hora, profesional, valores, conclusion)
            dao.guardar_estado(muestra)
            return resultado_id

    def emitir_comprobante(self, consulta_id, fecha):
        """Factura la consulta y sus análisis realizados que todavía no se hayan facturado.

        Las muestras rechazadas nunca se facturan. Un análisis que termina después
        se puede facturar en otro comprobante de la misma consulta.
        """
        with self._transaccion() as conexion:
            validar_fecha_hora(fecha, "Fecha del comprobante")
            consulta_dao = ConsultaDAO(conexion)
            consulta = self._exigir(consulta_dao.obtener_por_id(consulta_id), "La consulta no existe")
            dao = ComprobanteDAO(conexion)
            lineas = []
            if not dao.consulta_facturada(consulta_id):
                lineas.append((consulta_id, None, f"{consulta['tipo']} del {consulta['fecha_hora']}", consulta["precio"]))
            for analisis in dao.listar_analisis_a_facturar(consulta_id):
                lineas.append((None, analisis["id"], f"{analisis['analisis']} ({analisis['codigo']})", analisis["precio"]))
            if not lineas:
                raise ErrorNegocio("La consulta no tiene servicios pendientes de facturar")
            total = sum(linea[3] for linea in lineas)
            numero = dao.siguiente_numero()
            comprobante_id = dao.crear(numero, consulta_dao.obtener_cliente_id(consulta_id),
                                       consulta["clinica_id"], fecha, total)
            for detalle_consulta, detalle_muestra, descripcion, precio in lineas:
                dao.agregar_detalle(comprobante_id, detalle_consulta, detalle_muestra, descripcion, 1, precio)
            return {"comprobante_id": comprobante_id, "numero": numero, "total": total}

    def obtener_comprobante(self, comprobante_id):
        with self._transaccion() as conexion:
            dao = ComprobanteDAO(conexion)
            comprobante = self._exigir(dao.obtener_por_id(comprobante_id), "El comprobante no existe")
            return {"comprobante": comprobante, "detalles": dao.listar_detalles(comprobante_id)}
