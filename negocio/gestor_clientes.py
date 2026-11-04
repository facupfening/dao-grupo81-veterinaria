from dao.cliente_dao import ClienteDAO
from dao.mascota_dao import MascotaDAO
from modelos.cliente import Cliente
from negocio.gestor import ErrorNegocio, Gestor


class GestorClientes(Gestor):
    def alta(self, dni, nombre, apellido, telefono=None, email=None, direccion=None):
        with self._transaccion() as conexion:
            dao = ClienteDAO(conexion)
            cliente = Cliente(dni, nombre, apellido, telefono, email, direccion)
            if dao.obtener_por_dni(cliente.dni):
                raise ErrorNegocio(f"Ya existe un cliente con DNI {cliente.dni}")
            return dao.crear(cliente)

    def modificar(self, id, dni, nombre, apellido, telefono=None, email=None, direccion=None):
        with self._transaccion() as conexion:
            dao = ClienteDAO(conexion)
            self._exigir(dao.obtener_por_id(id), "El cliente no existe")
            cliente = Cliente(dni, nombre, apellido, telefono, email, direccion, id)
            otro = dao.obtener_por_dni(cliente.dni)
            if otro and otro.id != id:
                raise ErrorNegocio(f"Ya existe un cliente con DNI {cliente.dni}")
            dao.actualizar(cliente)

    def baja(self, id):
        with self._transaccion() as conexion:
            self._exigir(ClienteDAO(conexion).obtener_por_id(id), "El cliente no existe")
            if MascotaDAO(conexion).listar_por_cliente(id):
                raise ErrorNegocio("No se puede dar de baja un cliente con mascotas asociadas")
            ClienteDAO(conexion).eliminar(id)

    def obtener(self, id):
        with self._transaccion() as conexion:
            return ClienteDAO(conexion).obtener_por_id(id)

    def obtener_por_dni(self, dni):
        with self._transaccion() as conexion:
            return ClienteDAO(conexion).obtener_por_dni(dni)

    def listar(self):
        with self._transaccion() as conexion:
            return ClienteDAO(conexion).listar()

    def buscar_por_apellido(self, apellido):
        with self._transaccion() as conexion:
            return ClienteDAO(conexion).buscar_por_apellido(apellido)
