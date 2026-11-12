import flet as ft

from interfaz.pantalla import (COLOR_PRINCIPAL, Pantalla, campo_fecha, fila_de_tabla, formulario, lista, opcion, subtitulo,
                               tabla, tarjeta, texto_o_none)
from negocio.gestor import ErrorNegocio
from negocio.gestor_reportes import NOMBRES_REPORTES, GestorReportes


class PantallaReportes(Pantalla):
    titulo = "Reportes"

    def __init__(self, ruta):
        super().__init__()
        self.gestor = GestorReportes(ruta)
        self.tipo = lista("Reporte", [opcion(clave, nombre) for clave, nombre in NOMBRES_REPORTES.items()], ancho=460)
        self.desde = campo_fecha("Desde", con_hora=False, opcional=True)
        self.hasta = campo_fecha("Hasta", con_hora=False, opcional=True, desde=self.desde)
        self.resultado = ft.Column(spacing=10, controls=[ft.Text("Elegí un reporte y tocá Ver reporte.")])

    def controles(self):
        return [
            tarjeta(
                formulario(self.tipo, self.desde, self.hasta),
                ft.Row(controls=[
                    ft.FilledButton("Ver reporte", icon=ft.Icons.VISIBILITY, on_click=self.ver,
                                    bgcolor=COLOR_PRINCIPAL),
                    ft.OutlinedButton("Exportar a PDF", icon=ft.Icons.PICTURE_AS_PDF, on_click=self.exportar),
                ]),
            ),
            tarjeta(self.resultado),
        ]

    def ver(self, e):
        self._intentar(self._ver)

    def _ver(self):
        reporte = self._generar()
        controles = []
        for datos in reporte.tablas:
            controles.append(subtitulo(datos.subtitulo))
            if datos.filas:
                resultado = tabla(*datos.columnas)
                resultado.rows = [fila_de_tabla(fila) for fila in datos.filas]
                controles.append(ft.Row(controls=[resultado], scroll=ft.ScrollMode.AUTO))
            else:
                controles.append(ft.Text("Sin datos para el período elegido."))
        self.resultado.controls = controles
        self._informar(f"Período: {reporte.periodo}. Los gráficos se incluyen en el PDF.")

    def exportar(self, e):
        self._intentar(self._exportar)

    def _exportar(self):
        ruta = self.gestor.exportar_pdf(self.tipo.value, self._generar())
        self._informar(f"PDF guardado en {ruta}")

    def _generar(self):
        if not self.tipo.value:
            raise ErrorNegocio("Debe seleccionar: Reporte")
        return self.gestor.generar(self.tipo.value, texto_o_none(self.desde), texto_o_none(self.hasta))
