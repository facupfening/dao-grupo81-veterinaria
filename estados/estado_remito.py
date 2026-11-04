from abc import ABC, abstractmethod

from estados.transicion_invalida import TransicionInvalida

PRECINTO_INTACTO = "Intacto"
PRECINTO_ROTO = "Roto"


class EstadoRemito(ABC):
    """Por defecto ninguna operación está permitida.

    Cada estado concreto redefine solo las transiciones que admite.
    """

    @property
    @abstractmethod
    def nombre(self):
        pass

    def agregar_muestra(self, remito, muestra, fecha_hora, responsable, observacion=None):
        self._rechazar("agregar muestras a")

    def despachar(self, remito, fecha_hora, responsable, observacion=None):
        self._rechazar("despachar")

    def registrar_tramo(self, remito, fecha_hora, responsable, observacion=None):
        self._rechazar("registrar un tramo de")

    def registrar_recepcion(self, remito, estado_precinto, fecha_hora, responsable, observacion=None):
        self._rechazar("recibir")

    def _rechazar(self, accion):
        raise TransicionInvalida(f"No se puede {accion} un remito en estado {self.nombre}")


class Emitido(EstadoRemito):
    @property
    def nombre(self):
        return "Emitido"

    def agregar_muestra(self, remito, muestra, fecha_hora, responsable, observacion=None):
        muestra.empaquetar(fecha_hora, responsable, observacion)
        remito.incorporar_muestra(muestra)

    def despachar(self, remito, fecha_hora, responsable, observacion=None):
        if not remito.muestras:
            raise TransicionInvalida("No se puede despachar un remito sin muestras")
        remito.cambiar_estado(Despachado(), fecha_hora, responsable, observacion)


class Despachado(EstadoRemito):
    @property
    def nombre(self):
        return "Despachado"

    def registrar_tramo(self, remito, fecha_hora, responsable, observacion=None):
        remito.verificar_muestras("Empaquetada", fecha_hora)
        remito.cambiar_estado(EnTransito(), fecha_hora, responsable, observacion)
        for muestra in remito.muestras:
            muestra.iniciar_transito(fecha_hora, responsable, observacion)


class EnTransito(EstadoRemito):
    @property
    def nombre(self):
        return "En tránsito"

    def registrar_tramo(self, remito, fecha_hora, responsable, observacion=None):
        # Un traspaso o un arribo más: el remito sigue en tránsito, sin cambio de estado.
        pass

    def registrar_recepcion(self, remito, estado_precinto, fecha_hora, responsable, observacion=None):
        if estado_precinto not in (PRECINTO_INTACTO, PRECINTO_ROTO):
            raise ValueError(f"Estado de precinto inválido: {estado_precinto}")
        remito.verificar_muestras("En tránsito", fecha_hora)
        if estado_precinto == PRECINTO_INTACTO:
            remito.cambiar_estado(Recibido(), fecha_hora, responsable, observacion)
            for muestra in remito.muestras:
                muestra.recibir(fecha_hora, responsable, observacion)
        else:
            remito.cambiar_estado(Rechazado(), fecha_hora, responsable, observacion)
            for muestra in remito.muestras:
                muestra.rechazar(fecha_hora, responsable, observacion)


class Recibido(EstadoRemito):
    @property
    def nombre(self):
        return "Recibido"


class Rechazado(EstadoRemito):
    @property
    def nombre(self):
        return "Rechazado"


ESTADOS_REMITO = {
    "Emitido": Emitido,
    "Despachado": Despachado,
    "En tránsito": EnTransito,
    "Recibido": Recibido,
    "Rechazado": Rechazado,
}
