"""Creadores del patrón Factory Method: un exportador por cada formato.

Exportador.exportar() tiene los pasos comunes a todos los formatos. El único paso que cambia es qué documento
se crea, y eso lo decide cada subclase en su método fábrica crear_documento().
"""
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from reportes.documentos import DocumentoExcel, DocumentoMarkdown, DocumentoPDF

CARPETA_SALIDA = Path(__file__).parent.parent / "reportes_generados"


class Exportador(ABC):
    """Creador abstracto."""

    extension = ""

    def exportar(self, reporte, nombre_archivo, carpeta=CARPETA_SALIDA):
        """Guarda el reporte y devuelve la ruta. Cada archivo lleva fecha y hora para no pisar otro."""
        carpeta = Path(carpeta)
        carpeta.mkdir(parents=True, exist_ok=True)
        ruta = carpeta / f"{nombre_archivo}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.{self.extension}"
        documento = self.crear_documento(ruta)  # método fábrica: la subclase decide qué documento usar
        documento.agregar_encabezado(reporte.titulo, reporte.periodo)
        for tabla in reporte.tablas:
            documento.agregar_tabla(tabla)
        for grafico in reporte.graficos:
            documento.agregar_grafico(grafico)
        documento.guardar()
        return ruta

    @abstractmethod
    def crear_documento(self, ruta):
        """Método fábrica: devuelve el Documento del formato de esta subclase."""


class ExportadorPDF(Exportador):
    extension = "pdf"

    def crear_documento(self, ruta):
        return DocumentoPDF(ruta)


class ExportadorExcel(Exportador):
    extension = "xlsx"

    def crear_documento(self, ruta):
        return DocumentoExcel(ruta)


class ExportadorMarkdown(Exportador):
    extension = "md"

    def crear_documento(self, ruta):
        return DocumentoMarkdown(ruta)


# Formato elegido en pantalla -> clase que lo exporta.
EXPORTADORES = {
    "PDF": ExportadorPDF,
    "Excel": ExportadorExcel,
    "Markdown": ExportadorMarkdown,
}
