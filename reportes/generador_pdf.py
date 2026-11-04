from datetime import datetime
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import matplotlib

# Dibuja sin abrir ventanas: los gráficos solo se guardan como imagen dentro del PDF.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

CARPETA_SALIDA = Path(__file__).parent.parent / "reportes_generados"
COLOR_PRINCIPAL = colors.HexColor("#1F4E79")


def generar_pdf(reporte, nombre_archivo, carpeta=CARPETA_SALIDA):
    """Genera el PDF del reporte y devuelve su ruta. Cada archivo lleva fecha y hora para no pisar otro."""
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{nombre_archivo}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"
    documento = SimpleDocTemplate(str(ruta), pagesize=landscape(A4), title=reporte.titulo,
                                  leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    documento.build(_armar_elementos(reporte, documento.width))
    return ruta


def _armar_elementos(reporte, ancho):
    estilos = getSampleStyleSheet()
    elementos = [
        Paragraph(escape(reporte.titulo), estilos["Title"]),
        Paragraph(f"Período: {escape(reporte.periodo)}", estilos["Normal"]),
        Paragraph(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}", estilos["Normal"]),
        Spacer(1, 12),
    ]
    for tabla in reporte.tablas:
        elementos.append(Paragraph(escape(tabla.subtitulo), estilos["Heading3"]))
        elementos.append(_armar_tabla(tabla, ancho, estilos))
        elementos.append(Spacer(1, 12))
    for grafico in reporte.graficos:
        elementos.append(Image(_dibujar_grafico(grafico), width=480, height=240))
        elementos.append(Spacer(1, 12))
    return elementos


def _armar_tabla(tabla, ancho, estilos):
    if not tabla.filas:
        return Paragraph("Sin datos para el período elegido.", estilos["Normal"])
    encabezado = ParagraphStyle("encabezado", parent=estilos["Normal"], textColor=colors.white,
                                fontName="Helvetica-Bold")
    datos = [[Paragraph(escape(columna), encabezado) for columna in tabla.columnas]]
    for fila in tabla.filas:
        datos.append([Paragraph(escape("" if valor is None else str(valor)), estilos["Normal"]) for valor in fila])
    resultado = Table(datos, colWidths=[ancho / len(tabla.columnas)] * len(tabla.columnas), repeatRows=1)
    resultado.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRINCIPAL),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.whitesmoke]),
    ]))
    return resultado


def _dibujar_grafico(grafico):
    figura, ejes = plt.subplots(figsize=(8, 4))
    ejes.bar(grafico.etiquetas, grafico.valores, color="#1F4E79")
    ejes.set_title(grafico.titulo)
    ejes.set_ylabel(grafico.unidad)
    ejes.tick_params(axis="x", labelrotation=15)
    if all(isinstance(valor, int) for valor in grafico.valores):
        # Una cantidad no puede tener decimales en el eje.
        ejes.yaxis.set_major_locator(MaxNLocator(integer=True))
    figura.tight_layout()
    buffer = BytesIO()
    figura.savefig(buffer, format="png", dpi=150)
    plt.close(figura)
    buffer.seek(0)
    return buffer
