class RegistroEstado:
    """Una entrada del historial de estados. Solo se puede consultar, nunca modificar."""

    def __init__(self, estado, fecha_hora, responsable, observacion=None):
        if not fecha_hora:
            raise ValueError("La fecha y hora del cambio de estado es obligatoria")
        if not responsable:
            raise ValueError("El responsable del cambio de estado es obligatorio")
        self._estado = estado
        self._fecha_hora = fecha_hora
        self._responsable = responsable
        self._observacion = observacion

    @property
    def estado(self):
        return self._estado

    @property
    def fecha_hora(self):
        return self._fecha_hora

    @property
    def responsable(self):
        return self._responsable

    @property
    def observacion(self):
        return self._observacion

    def __str__(self):
        return f"{self._fecha_hora} - {self._estado} ({self._responsable})"
