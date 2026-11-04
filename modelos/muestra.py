from estados.estado_muestra import ESTADOS_MUESTRA
from modelos.trazable import Trazable


class Muestra(Trazable):
    """Muestra biológica. Las operaciones se delegan en su estado actual."""

    def __init__(self, codigo, orden_id, tipo_analisis_id, fecha_extraccion, responsable=None,
                 estado="Extraída", historial=None, id=None):
        super().__init__(ESTADOS_MUESTRA[estado](), fecha_extraccion, responsable, historial)
        self.id = id
        self.codigo = codigo
        self.orden_id = orden_id
        self.tipo_analisis_id = tipo_analisis_id
        self.fecha_extraccion = fecha_extraccion

    def empaquetar(self, fecha_hora, responsable, observacion=None):
        self._estado.empaquetar(self, fecha_hora, responsable, observacion)

    def iniciar_transito(self, fecha_hora, responsable, observacion=None):
        self._estado.iniciar_transito(self, fecha_hora, responsable, observacion)

    def recibir(self, fecha_hora, responsable, observacion=None):
        self._estado.recibir(self, fecha_hora, responsable, observacion)

    def rechazar(self, fecha_hora, responsable, observacion=None):
        self._estado.rechazar(self, fecha_hora, responsable, observacion)

    def analizar(self, fecha_hora, responsable, observacion=None):
        self._estado.analizar(self, fecha_hora, responsable, observacion)

    def __str__(self):
        return f"Muestra {self.codigo} ({self.estado})"
