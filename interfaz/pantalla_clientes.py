import flet as ft

from interfaz.pantalla import (SOLO_DIGITOS, TELEFONO, Dialogo, Pantalla, boton_nuevo, campo, fila_de_tabla, formulario, subtitulo, tabla,
                               tarjeta, texto_o_none, vaciar)
from negocio.gestor_clientes import GestorClientes


class PantallaClientes(Pantalla):
    titulo = "Clientes"

    def __init__(self, ruta):
        super().__init__()
        self.gestor = GestorClientes(ruta)
        self.id_en_edicion = None
        self.dni = campo("DNI *", input_filter=SOLO_DIGITOS, max_length=8)
        self.nombre = campo("Nombre *")
        self.apellido = campo("Apellido *")
        self.telefono = campo("Teléfono", input_filter=TELEFONO)
        self.email = campo("Email")
        self.direccion = campo("Dirección")
        self.busqueda = campo("Buscar por apellido")
        self.tabla = tabla("DNI", "Apellido", "Nombre", "Teléfono", "Email", "Dirección", "Acciones")
        self.dialogo = Dialogo(
            "Nuevo cliente",
            [formulario(self.dni, self.nombre, self.apellido, self.telefono, self.email, self.direccion)],
            self.guardar,
        )

    def controles(self):
        return [
            ft.Row(controls=[boton_nuevo("Nuevo cliente", self.nuevo)]),
            tarjeta(
                subtitulo("Listado"),
                ft.Row(controls=[self.busqueda, ft.OutlinedButton("Buscar", icon=ft.Icons.SEARCH, on_click=self.buscar)]),
                ft.Row(controls=[self.tabla], scroll=ft.ScrollMode.AUTO),
            ),
        ]

    def refrescar(self):
        self._mostrar(self.gestor.listar())

    def nuevo(self, e):
        self._vaciar()
        self._abrir_dialogo(self.dialogo, "Nuevo cliente")

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
        self._cerrar_dialogo()
        self._vaciar()
        self.refrescar()

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
        self._abrir_dialogo(self.dialogo, f"Editar cliente {cliente.apellido}, {cliente.nombre}")

    def borrar(self, cliente):
        self._intentar(lambda: self._borrar(cliente))

    def _borrar(self, cliente):
        self.gestor.baja(cliente.id)
        self._informar(f"Cliente {cliente.apellido}, {cliente.nombre} dado de baja.")
        self.refrescar()

    def _vaciar(self):
        self.id_en_edicion = None
        vaciar(self.dni, self.nombre, self.apellido, self.telefono, self.email, self.direccion)

    def _mostrar(self, clientes):
        # c=c fija el cliente de cada fila: sin eso, todos los botones usarían el último cliente.
        self.tabla.rows = [
            fila_de_tabla(
                [c.dni, c.apellido, c.nombre, c.telefono, c.email, c.direccion],
                [
                    ft.IconButton(ft.Icons.EDIT, tooltip="Editar", icon_color=ft.Colors.BLUE_700,
                                  on_click=lambda e, c=c: self.editar(c)),
                    ft.IconButton(ft.Icons.DELETE, tooltip="Dar de baja", icon_color=ft.Colors.RED_700,
                                  on_click=lambda e, c=c: self.borrar(c)),
                ],
            )
            for c in clientes
        ]
