from abc import ABC, abstractmethod

from estados.transicion_invalida import TransicionInvalida


class EstadoMuestra(ABC):
    """Por defecto ninguna operación está permitida.

    Cada estado concreto redefine solo las transiciones que admite.
    """

    @property
    @abstractmethod
    def nombre(self):
        pass

    def empaquetar(self, muestra, fecha_hora, responsable, observacion=None):
        self._rechazar("empaquetar")

    def iniciar_transito(self, muestra, fecha_hora, responsable, observacion=None):
        self._rechazar("despachar")

    def recibir(self, muestra, fecha_hora, responsable, observacion=None):
        self._rechazar("recibir")

    def rechazar(self, muestra, fecha_hora, responsable, observacion=None):
        self._rechazar("rechazar")

    def analizar(self, muestra, fecha_hora, responsable, observacion=None):
        self._rechazar("analizar")

    def _rechazar(self, accion):
        raise TransicionInvalida(f"No se puede {accion} una muestra en estado {self.nombre}")


class Extraida(EstadoMuestra):
    @property
    def nombre(self):
        return "Extraída"

    def empaquetar(self, muestra, fecha_hora, responsable, observacion=None):
        muestra.cambiar_estado(Empaquetada(), fecha_hora, responsable, observacion)


class Empaquetada(EstadoMuestra):
    @property
    def nombre(self):
        return "Empaquetada"

    def iniciar_transito(self, muestra, fecha_hora, responsable, observacion=None):
        muestra.cambiar_estado(EnTransito(), fecha_hora, responsable, observacion)


class EnTransito(EstadoMuestra):
    @property
    def nombre(self):
        return "En tránsito"

    def recibir(self, muestra, fecha_hora, responsable, observacion=None):
        muestra.cambiar_estado(Recibida(), fecha_hora, responsable, observacion)

    def rechazar(self, muestra, fecha_hora, responsable, observacion=None):
        muestra.cambiar_estado(Rechazada(), fecha_hora, responsable, observacion)


class Recibida(EstadoMuestra):
    @property
    def nombre(self):
        return "Recibida"

    def analizar(self, muestra, fecha_hora, responsable, observacion=None):
        muestra.cambiar_estado(Analizada(), fecha_hora, responsable, observacion)


class Analizada(EstadoMuestra):
    @property
    def nombre(self):
        return "Analizada"


class Rechazada(EstadoMuestra):
    @property
    def nombre(self):
        return "Rechazada"


ESTADOS_MUESTRA = {
    "Extraída": Extraida,
    "Empaquetada": Empaquetada,
    "En tránsito": EnTransito,
    "Recibida": Recibida,
    "Analizada": Analizada,
    "Rechazada": Rechazada,
}
