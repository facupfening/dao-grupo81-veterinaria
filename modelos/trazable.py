from modelos.registro_estado import RegistroEstado


class Trazable:
    """Contexto del patrón State: guarda el estado actual y su historial.

    El historial solo crece: no hay forma de quitar ni de reemplazar registros.
    """

    def __init__(self, estado, fecha_hora, responsable, historial):
        self._estado = estado
        if historial is None:
            # Objeto nuevo: su primer estado también queda registrado.
            self._historial = [RegistroEstado(estado.nombre, fecha_hora, responsable)]
        else:
            # Objeto recuperado de la base con el historial que ya tenía.
            self._historial = list(historial)

    @property
    def estado(self):
        return self._estado.nombre

    @property
    def historial(self):
        return tuple(self._historial)

    def cambiar_estado(self, estado_nuevo, fecha_hora, responsable, observacion=None):
        registro = RegistroEstado(estado_nuevo.nombre, fecha_hora, responsable, observacion)
        if self._historial and fecha_hora < self._historial[-1].fecha_hora:
            raise ValueError("La fecha del cambio de estado no puede ser anterior a la del último registro")
        self._estado = estado_nuevo
        self._historial.append(registro)
