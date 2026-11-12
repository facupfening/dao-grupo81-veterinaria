"""Productos del patrón Factory Method: un tipo de documento por cada formato de exportación.

Todos se arman igual (encabezado, tablas, gráficos y guardar); cada uno sabe cómo se escribe en su formato.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from xml.sax.saxutils import escape

from openpyxl import Workbook
from openpyxl.drawing.image import Image as ImagenExcel
from openpyxl.styles import Font
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from reportes.grafico import dibujar_grafico

SIN_DATOS = "Sin datos para el período elegido."
COLOR_PRINCIPAL = colors.HexColor("#1F4E79")


def _generado():
    return f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}"


def _texto(valor):
    return "" if valor is None else str(valor)


class Documento(ABC):
    """Producto abstracto: un archivo de reporte que se arma por partes."""

    def __init__(self, ruta):
        self.ruta = ruta

    @abstractmethod
    def agregar_encabezado(self, titulo, periodo):
        pass

    @abstractmethod
    def agregar_tabla(self, tabla):
        pass

    @abstractmethod
    def agregar_grafico(self, grafico):
        pass

    @abstractmethod
    def guardar(self):
        pass


class DocumentoPDF(Documento):
    """PDF apaisado (reportlab): tablas con encabezado de color y los gráficos como imágenes."""

    def __init__(self, ruta):
        super().__init__(ruta)
        self.pdf = SimpleDocTemplate(str(ruta), pagesize=landscape(A4),
                                     leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
        self.estilos = getSampleStyleSheet()
        self.elementos = []

    def agregar_encabezado(self, titulo, periodo):
        self.pdf.title = titulo
        self.elementos += [
            Paragraph(escape(titulo), self.estilos["Title"]),
            Paragraph(f"Período: {escape(periodo)}", self.estilos["Normal"]),
            Paragraph(_generado(), self.estilos["Normal"]),
            Spacer(1, 12),
        ]

    def agregar_tabla(self, tabla):
        self.elementos.append(Paragraph(escape(tabla.subtitulo), self.estilos["Heading3"]))
        if tabla.filas:
            self.elementos.append(self._armar_tabla(tabla))
        else:
            self.elementos.append(Paragraph(SIN_DATOS, self.estilos["Normal"]))
        self.elementos.append(Spacer(1, 12))

    def agregar_grafico(self, grafico):
        self.elementos += [Image(dibujar_grafico(grafico), width=480, height=240), Spacer(1, 12)]

    def guardar(self):
        self.pdf.build(self.elementos)

    def _armar_tabla(self, tabla):
        encabezado = ParagraphStyle("encabezado", parent=self.estilos["Normal"], textColor=colors.white,
                                    fontName="Helvetica-Bold")
        datos = [[Paragraph(escape(columna), encabezado) for columna in tabla.columnas]]
        for fila in tabla.filas:
            datos.append([Paragraph(escape(_texto(valor)), self.estilos["Normal"]) for valor in fila])
        ancho = self.pdf.width / len(tabla.columnas)
        resultado = Table(datos, colWidths=[ancho] * len(tabla.columnas), repeatRows=1)
        resultado.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRINCIPAL),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.whitesmoke]),
        ]))
        return resultado


class DocumentoExcel(Documento):
    """Libro de Excel (openpyxl): las tablas en la hoja "Datos" y los gráficos en la hoja "Gráficos"."""

    FILAS_POR_GRAFICO = 18  # cada imagen ocupa unas 17 filas; se deja una de separación

    def __init__(self, ruta):
        super().__init__(ruta)
        self.libro = Workbook()
        self.datos = self.libro.active
        self.datos.title = "Datos"
        self.graficos = self.libro.create_sheet("Gráficos")
        self.cantidad_graficos = 0

    def agregar_encabezado(self, titulo, periodo):
        self.datos.append([titulo])
        self._ultima_fila_en_negrita(tamanio=14)
        self.datos.append([f"Período: {periodo}"])
        self.datos.append([_generado()])
        self.datos.append([])

    def agregar_tabla(self, tabla):
        self.datos.append([tabla.subtitulo])
        self._ultima_fila_en_negrita(tamanio=12)
        if tabla.filas:
            self.datos.append(tabla.columnas)
            self._ultima_fila_en_negrita()
            for fila in tabla.filas:
                self.datos.append(list(fila))
        else:
            self.datos.append([SIN_DATOS])
        self.datos.append([])

    def agregar_grafico(self, grafico):
        imagen = ImagenExcel(dibujar_grafico(grafico))
        imagen.width, imagen.height = 640, 320
        fila = 1 + self.cantidad_graficos * self.FILAS_POR_GRAFICO
        self.graficos.add_image(imagen, f"A{fila}")
        self.cantidad_graficos += 1

    def guardar(self):
        if self.cantidad_graficos == 0:
            self.graficos["A1"] = SIN_DATOS
        for columna in "ABCDEFGH":
            self.datos.column_dimensions[columna].width = 24
        self.libro.save(self.ruta)

    def _ultima_fila_en_negrita(self, tamanio=11):
        for celda in self.datos[self.datos.max_row]:
            celda.font = Font(bold=True, size=tamanio)


class DocumentoMarkdown(Documento):
    """Texto Markdown (.md). Markdown no guarda imágenes adentro: cada gráfico va en un PNG al lado y el .md lo enlaza."""

    def __init__(self, ruta):
        super().__init__(ruta)
        self.lineas = []
        self.cantidad_graficos = 0

    def agregar_encabezado(self, titulo, periodo):
        self.lineas += [f"# {titulo}", "", f"Período: {periodo}", "", _generado(), ""]

    def agregar_tabla(self, tabla):
        self.lineas += [f"## {tabla.subtitulo}", ""]
        if tabla.filas:
            self.lineas.append(self._fila(tabla.columnas))
            self.lineas.append(self._fila(["---"] * len(tabla.columnas)))
            for fila in tabla.filas:
                self.lineas.append(self._fila(fila))
        else:
            self.lineas.append(SIN_DATOS)
        self.lineas.append("")

    def agregar_grafico(self, grafico):
        self.cantidad_graficos += 1
        if self.cantidad_graficos == 1:
            self.lineas += ["## Gráficos", ""]
        imagen = self.ruta.with_name(f"{self.ruta.stem}_grafico_{self.cantidad_graficos}.png")
        imagen.write_bytes(dibujar_grafico(grafico).getvalue())
        self.lineas += [f"![{grafico.titulo}]({imagen.name})", ""]

    def guardar(self):
        self.ruta.write_text("\n".join(self.lineas), encoding="utf-8")

    def _fila(self, valores):
        """Una fila de tabla Markdown: | a | b |. La barra | dentro de un dato se escapa para no cortar la celda."""
        return "| " + " | ".join(_texto(valor).replace("|", "\\|") for valor in valores) + " |"
