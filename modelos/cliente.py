from modelos.validaciones import validar_obligatorio


class Cliente:
    """Responsable de una o más mascotas."""

    def __init__(self, dni, nombre, apellido, telefono=None, email=None, direccion=None, id=None):
        self.id = id
        self.dni = dni
        self.nombre = nombre
        self.apellido = apellido
        self.telefono = telefono
        self.email = email
        self.direccion = direccion

    @property
    def dni(self):
        return self._dni

    @dni.setter
    def dni(self, valor):
        dni = validar_obligatorio(valor, "DNI")
        if not dni.isdigit() or not 7 <= len(dni) <= 8:
            raise ValueError("DNI: debe tener 7 u 8 dígitos")
        self._dni = dni

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        self._nombre = validar_obligatorio(valor, "Nombre")

    @property
    def apellido(self):
        return self._apellido

    @apellido.setter
    def apellido(self, valor):
        self._apellido = validar_obligatorio(valor, "Apellido")

    def __str__(self):
        return f"{self.apellido}, {self.nombre} (DNI {self.dni})"
