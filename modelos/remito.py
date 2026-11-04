from estados.estado_remito import ESTADOS_REMITO
from estados.transicion_invalida import TransicionInvalida
from modelos.trazable import Trazable


class Remito(Trazable):
    """Remito biológico: agrupa las muestras que viajan en una misma conservadora."""

    def __init__(self, numero, clinica_id, laboratorio_id, conservadora_id, fecha_emision,
                 responsable=None, estado="Emitido", historial=None, muestras=None, id=None):
        super().__init__(ESTADOS_REMITO[estado](), fecha_emision, responsable, historial)
        self.id = id
        self.numero = numero
        self.clinica_id = clinica_id
        self.laboratorio_id = laboratorio_id
        self.conservadora_id = conservadora_id
        self.fecha_emision = fecha_emision
        self._muestras = list(muestras) if muestras else []

    @property
    def muestras(self):
        return tuple(self._muestras)

    def agregar_muestra(self, muestra, fecha_hora, responsable, observacion=None):
        self._estado.agregar_muestra(self, muestra, fecha_hora, responsable, observacion)

    def despachar(self, fecha_hora, responsable, observacion=None):
        self._estado.despachar(self, fecha_hora, responsable, observacion)

    def registrar_tramo(self, fecha_hora, responsable, observacion=None):
        """Registra un traspaso o un arribo posterior al despacho."""
        self._estado.registrar_tramo(self, fecha_hora, responsable, observacion)

    def registrar_recepcion(self, estado_precinto, fecha_hora, responsable, observacion=None):
        """Con el precinto intacto el remito se recibe; con el precinto roto se rechaza."""
        self._estado.registrar_recepcion(self, estado_precinto, fecha_hora, responsable, observacion)

    def incorporar_muestra(self, muestra):
        self._muestras.append(muestra)

    def verificar_muestras(self, estado_esperado, fecha_hora):
        """Evita cambiar el remito si alguna de sus muestras no puede acompañar la transición."""
        for muestra in self._muestras:
            if muestra.estado != estado_esperado:
                raise TransicionInvalida(
                    f"La muestra {muestra.codigo} está en estado {muestra.estado} y debería estar en {estado_esperado}"
                )
            if fecha_hora < muestra.historial[-1].fecha_hora:
                raise ValueError(f"La fecha no puede ser anterior al último registro de la muestra {muestra.codigo}")

    def __str__(self):
        return f"Remito {self.numero} ({self.estado})"
