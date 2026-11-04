from modelos.validaciones import validar_fecha, validar_obligatorio


class Mascota:
    """Toda mascota tiene un cliente responsable y una especie."""

    def __init__(self, cliente_id, especie_id, nombre, raza=None, sexo=None,
                 fecha_nacimiento=None, peso_kg=None, id=None):
        self.id = id
        self.cliente_id = cliente_id
        self.especie_id = especie_id
        self.nombre = nombre
        self.raza = raza
        self.sexo = sexo
        self.fecha_nacimiento = fecha_nacimiento
        self.peso_kg = peso_kg

    @property
    def cliente_id(self):
        return self._cliente_id

    @cliente_id.setter
    def cliente_id(self, valor):
        if not valor:
            raise ValueError("Toda mascota debe tener un responsable")
        self._cliente_id = valor

    @property
    def especie_id(self):
        return self._especie_id

    @especie_id.setter
    def especie_id(self, valor):
        if not valor:
            raise ValueError("Toda mascota debe tener una especie")
        self._especie_id = valor

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        self._nombre = validar_obligatorio(valor, "Nombre")

    @property
    def fecha_nacimiento(self):
        return self._fecha_nacimiento

    @fecha_nacimiento.setter
    def fecha_nacimiento(self, valor):
        if valor:
            validar_fecha(valor, "Fecha de nacimiento")
        self._fecha_nacimiento = valor or None

    @property
    def peso_kg(self):
        return self._peso_kg

    @peso_kg.setter
    def peso_kg(self, valor):
        if valor is not None and valor <= 0:
            raise ValueError("Peso: debe ser mayor a cero")
        self._peso_kg = valor

    def __str__(self):
        return f"{self.nombre} ({self.raza or 'sin raza'})"
