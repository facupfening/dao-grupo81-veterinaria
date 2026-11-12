from datetime import datetime

from dao.mascota_dao import MascotaDAO
from dao.reporte_dao import ReporteDAO
from modelos.validaciones import FORMATO_FECHA_HORA, validar_fecha
from negocio.gestor import ErrorNegocio, Gestor
from negocio.gestor_atencion import GestorAtencion
from reportes.exportadores import CARPETA_SALIDA, EXPORTADORES
from reportes.reporte import Reporte

FORMATOS = list(EXPORTADORES)

ATENCIONES = "atenciones"
RECHAZOS = "rechazos"
TRATAMIENTOS = "tratamientos"
FACTURACION = "facturacion"
TIEMPOS = "tiempos"

NOMBRES_REPORTES = {
    ATENCIONES: "Atenciones clínicas y derivaciones",
    RECHAZOS: "Muestras rechazadas por fallas en el transporte",
    TRATAMIENTOS: "Tratamientos aplicados y vacunas pendientes",
    FACTURACION: "Facturación desglosada",
    TIEMPOS: "Tiempo promedio de tránsito y de procesamiento",
}


def _moneda(importe):
    return f"$ {importe:.2f}"


def _horas(valor):
    return f"{valor:.1f}"


class GestorReportes(Gestor):
    def generar(self, tipo, desde=None, hasta=None):
        """Arma el reporte pedido. Las fechas AAAA-MM-DD son opcionales e incluyen ambos extremos."""
        generadores = {
            ATENCIONES: self.atenciones,
            RECHAZOS: self.rechazos,
            TRATAMIENTOS: self.tratamientos_y_vacunas,
            FACTURACION: self.facturacion,
            TIEMPOS: self.tiempos,
        }
        if tipo not in generadores:
            raise ErrorNegocio(f"Reporte desconocido: {tipo}")
        return generadores[tipo](desde, hasta)

    def exportar(self, tipo, reporte, formato, carpeta=CARPETA_SALIDA):
        """Guarda el reporte en el formato elegido (PDF, Excel o Markdown) y devuelve la ruta del archivo."""
        if formato not in EXPORTADORES:
            raise ErrorNegocio(f"Formato desconocido: {formato}")
        exportador = EXPORTADORES[formato]()
        try:
            return exportador.exportar(reporte, tipo, carpeta)
        except OSError as error:
            raise ErrorNegocio(f"No se pudo guardar el archivo: {error}") from error

    def atenciones(self, desde=None, hasta=None):
        inicio, fin, reporte = self._preparar(ATENCIONES, desde, hasta)
        with self._transaccion() as conexion:
            filas = ReporteDAO(conexion).atenciones_por_clinica(inicio, fin)
        reporte.agregar_tabla(
            "Por clínica",
            ["Clínica", "Consultas", "Controles", "Urgencias", "Total de atenciones", "Órdenes emitidas"],
            [[f["clinica"], f["consultas"], f["controles"], f["urgencias"], f["total"], f["ordenes"]] for f in filas],
        )
        reporte.agregar_grafico("Atenciones por clínica", [f["clinica"] for f in filas],
                                [f["total"] for f in filas], "Atenciones")
        reporte.agregar_grafico("Órdenes de derivación por clínica", [f["clinica"] for f in filas],
                                [f["ordenes"] for f in filas], "Órdenes")
        return reporte

    def rechazos(self, desde=None, hasta=None):
        inicio, fin, reporte = self._preparar(RECHAZOS, desde, hasta)
        with self._transaccion() as conexion:
            filas = ReporteDAO(conexion).muestras_rechazadas(inicio, fin)
        cantidades = {}
        for fila in filas:
            clave = (fila["clinica"], fila["transportista"])
            cantidades[clave] = cantidades.get(clave, 0) + 1
        reporte.agregar_tabla(
            "Por clínica de origen y transportista",
            ["Clínica", "Transportista", "Muestras rechazadas"],
            [[clinica, transportista, cantidad] for (clinica, transportista), cantidad in cantidades.items()],
        )
        reporte.agregar_tabla(
            "Detalle de muestras",
            ["Clínica", "Transportista", "Remito", "Precinto", "Muestra", "Análisis", "Recepción"],
            [[f["clinica"], f["transportista"], f["remito"], f["precinto"], f["muestra"], f["analisis"], f["fecha"]]
             for f in filas],
        )
        reporte.agregar_grafico("Muestras rechazadas por clínica y transportista",
                                [f"{clinica} / {transportista}" for clinica, transportista in cantidades],
                                list(cantidades.values()), "Muestras")
        return reporte

    def tratamientos_y_vacunas(self, desde=None, hasta=None):
        """Las vacunas se evalúan al final del período o, si no se indica, a la fecha actual."""
        inicio, fin, reporte = self._preparar(TRATAMIENTOS, desde, hasta)
        referencia = fin if hasta else datetime.now().strftime(FORMATO_FECHA_HORA)
        with self._transaccion() as conexion:
            tratamientos = ReporteDAO(conexion).tratamientos(inicio, fin)
            mascotas = MascotaDAO(conexion).listar_detallado()
        reporte.agregar_tabla(
            "Tratamientos aplicados",
            ["Fecha", "Clínica", "Mascota", "Veterinario", "Diagnóstico", "Tratamiento"],
            [[f["fecha_hora"], f["clinica"], f["mascota"], f["veterinario"], f["diagnostico"], f["tratamiento"]]
             for f in tratamientos],
        )
        atencion = GestorAtencion(self._ruta)
        filas = []
        total_pendientes = total_vencidas = 0
        for mascota in mascotas:
            esquema = atencion.esquema_vacunas(mascota["id"], referencia)
            pendientes, vencidas = esquema["vacunas_pendientes"], esquema["vacunas_vencidas"]
            if pendientes or vencidas:
                filas.append([mascota["nombre"], mascota["especie"], mascota["responsable"],
                              ", ".join(pendientes) or "-", ", ".join(vencidas) or "-"])
                total_pendientes += len(pendientes)
                total_vencidas += len(vencidas)
        reporte.agregar_tabla(
            f"Vacunas obligatorias al {referencia[:10]}",
            ["Mascota", "Especie", "Responsable", "Faltantes", "Vencidas"],
            filas,
        )
        reporte.agregar_grafico("Vacunas obligatorias sin cubrir", ["Faltantes", "Vencidas"],
                                [total_pendientes, total_vencidas], "Dosis")
        return reporte

    def facturacion(self, desde=None, hasta=None):
        inicio, fin, reporte = self._preparar(FACTURACION, desde, hasta)
        with self._transaccion() as conexion:
            filas = ReporteDAO(conexion).facturacion(inicio, fin)
        totales = {}
        for fila in filas:
            total = totales.setdefault(fila["clinica"], {"consultas": 0, "laboratorio": 0})
            total["laboratorio" if fila["es_laboratorio"] else "consultas"] += fila["importe"]
        reporte.agregar_tabla(
            "Totales por clínica",
            ["Clínica", "Consultas", "Laboratorio", "Total"],
            [[clinica, _moneda(t["consultas"]), _moneda(t["laboratorio"]), _moneda(t["consultas"] + t["laboratorio"])]
             for clinica, t in totales.items()],
        )
        reporte.agregar_tabla(
            "Detalle por servicio",
            ["Clínica", "Servicio", "Cantidad", "Importe"],
            [[f["clinica"], f["concepto"], f["cantidad"], _moneda(f["importe"])] for f in filas],
        )
        reporte.agregar_grafico("Facturación total por clínica", list(totales),
                                [t["consultas"] + t["laboratorio"] for t in totales.values()], "Pesos")
        return reporte

    def tiempos(self, desde=None, hasta=None):
        inicio, fin, reporte = self._preparar(TIEMPOS, desde, hasta)
        with self._transaccion() as conexion:
            dao = ReporteDAO(conexion)
            transito = dao.tiempos_de_transito(inicio, fin)
            procesamiento = dao.tiempos_de_procesamiento(inicio, fin)
        reporte.agregar_tabla(
            "Tránsito: desde el despacho hasta la recepción",
            ["Clínica de origen", "Remitos", "Promedio (horas)"],
            self._filas_con_promedio_general(transito, "clinica"),
        )
        reporte.agregar_tabla(
            "Procesamiento: desde la recepción hasta el resultado",
            ["Tipo de análisis", "Muestras", "Promedio (horas)"],
            self._filas_con_promedio_general(procesamiento, "analisis"),
        )
        reporte.agregar_grafico("Tránsito promedio por clínica", [f["clinica"] for f in transito],
                                [f["horas"] for f in transito], "Horas")
        reporte.agregar_grafico("Procesamiento promedio por análisis", [f["analisis"] for f in procesamiento],
                                [f["horas"] for f in procesamiento], "Horas")
        return reporte

    def _filas_con_promedio_general(self, filas, columna):
        """El promedio general pondera por cantidad: no es el promedio de los promedios."""
        resultado = [[f[columna], f["cantidad"], _horas(f["horas"])] for f in filas]
        cantidad = sum(f["cantidad"] for f in filas)
        if cantidad:
            general = sum(f["horas"] * f["cantidad"] for f in filas) / cantidad
            resultado.append(["General", cantidad, _horas(general)])
        return resultado

    def _preparar(self, tipo, desde, hasta):
        if desde:
            validar_fecha_de_periodo(desde, "Desde")
        if hasta:
            validar_fecha_de_periodo(hasta, "Hasta")
        if desde and hasta and desde > hasta:
            raise ErrorNegocio("La fecha Desde no puede ser posterior a la fecha Hasta")
        inicio = f"{desde} 00:00" if desde else "0000-01-01 00:00"
        fin = f"{hasta} 23:59" if hasta else "9999-12-31 23:59"
        periodo = f"{desde or 'el inicio'} a {hasta or 'la fecha actual'}"
        return inicio, fin, Reporte(NOMBRES_REPORTES[tipo], periodo)


def validar_fecha_de_periodo(valor, campo):
    try:
        validar_fecha(valor, campo)
    except ValueError as error:
        raise ErrorNegocio(str(error)) from error
