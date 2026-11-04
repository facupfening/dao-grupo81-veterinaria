class TablaReporte:
    def __init__(self, subtitulo, columnas, filas):
        self.subtitulo = subtitulo
        self.columnas = columnas
        self.filas = filas


class GraficoReporte:
    def __init__(self, titulo, etiquetas, valores, unidad):
        self.titulo = titulo
        self.etiquetas = etiquetas
        self.valores = valores
        self.unidad = unidad


class Reporte:
    """Contenido de un reporte, independiente de si se muestra en pantalla o en un PDF."""

    def __init__(self, titulo, periodo):
        self.titulo = titulo
        self.periodo = periodo
        self._tablas = []
        self._graficos = []

    @property
    def tablas(self):
        return tuple(self._tablas)

    @property
    def graficos(self):
        return tuple(self._graficos)

    def agregar_tabla(self, subtitulo, columnas, filas):
        self._tablas.append(TablaReporte(subtitulo, columnas, filas))

    def agregar_grafico(self, titulo, etiquetas, valores, unidad):
        """Un gráfico sin valores no aporta información, así que no se agrega."""
        if any(valores):
            self._graficos.append(GraficoReporte(titulo, etiquetas, valores, unidad))
