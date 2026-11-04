import flet as ft

from interfaz.pantalla import Pantalla, campo, fila_de_tabla, formulario, subtitulo, tabla, texto_o_none
from negocio.gestor_clientes import GestorClientes


class PantallaClientes(Pantalla):
    titulo = "Clientes"

    def __init__(self, ruta):
        super().__init__()
        self.gestor = GestorClientes(ruta)
        self.id_en_edicion = None
        self.dni = campo("DNI")
        self.nombre = campo("Nombre")
        self.apellido = campo("Apellido")
        self.telefono = campo("Teléfono")
        self.email = campo("Email")
        self.direccion = campo("Dirección")
        self.busqueda = campo("Buscar por apellido")
        self.tabla = tabla("DNI", "Apellido", "Nombre", "Teléfono", "Email", "Dirección", "Acciones")

    def controles(self):
        return [
            formulario(self.dni, self.nombre, self.apellido, self.telefono, self.email, self.direccion),
            ft.Row(controls=[
                ft.Button("Guardar", on_click=self.guardar),
                ft.OutlinedButton("Limpiar", on_click=self.limpiar),
            ]),
            subtitulo("Listado"),
            ft.Row(controls=[self.busqueda, ft.OutlinedButton("Buscar", on_click=self.buscar)]),
            ft.Row(controls=[self.tabla], scroll=ft.ScrollMode.AUTO),
        ]

    def refrescar(self):
        self._mostrar(self.gestor.listar())

    def guardar(self, e):
        self._intentar(self._guardar)

    def _guardar(self):
        datos = (self.dni.value, self.nombre.value, self.apellido.value, texto_o_none(self.telefono),
                 texto_o_none(self.email), texto_o_none(self.direccion))
        if self.id_en_edicion:
            self.gestor.modificar(self.id_en_edicion, *datos)
            self._informar("Cliente modificado.")
        else:
            self.gestor.alta(*datos)
            self._informar("Cliente registrado.")
        self._vaciar()
        self.refrescar()

    def limpiar(self, e):
        self._vaciar()
        self.mensaje.value = ""

    def buscar(self, e):
        self._mostrar(self.gestor.buscar_por_apellido((self.busqueda.value or "").strip()))

    def editar(self, cliente):
        self.id_en_edicion = cliente.id
        self.dni.value = cliente.dni
        self.nombre.value = cliente.nombre
        self.apellido.value = cliente.apellido
        self.telefono.value = cliente.telefono or ""
        self.email.value = cliente.email or ""
        self.direccion.value = cliente.direccion or ""
        self.mensaje.value = ""

    def borrar(self, cliente):
        self._intentar(lambda: self._borrar(cliente))

    def _borrar(self, cliente):
        self.gestor.baja(cliente.id)
        self._informar(f"Cliente {cliente.apellido}, {cliente.nombre} dado de baja.")
        self.refrescar()

    def _vaciar(self):
        self.id_en_edicion = None
        for control in (self.dni, self.nombre, self.apellido, self.telefono, self.email, self.direccion):
            control.value = ""

    def _mostrar(self, clientes):
        self.tabla.rows = [
            fila_de_tabla(
                [c.dni, c.apellido, c.nombre, c.telefono, c.email, c.direccion],
                [
                    ft.IconButton(ft.Icons.EDIT, tooltip="Editar", on_click=lambda e, c=c: self.editar(c)),
                    ft.IconButton(ft.Icons.DELETE, tooltip="Dar de baja", on_click=lambda e, c=c: self.borrar(c)),
                ],
            )
            for c in clientes
        ]
