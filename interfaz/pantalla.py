from abc import ABC, abstractmethod
from datetime import datetime

import flet as ft

from modelos.validaciones import FORMATO_FECHA_HORA
from negocio.gestor import ErrorNegocio


def ahora():
    return datetime.now().strftime(FORMATO_FECHA_HORA)


def campo(etiqueta, valor="", ancho=230, **opciones):
    return ft.TextField(label=etiqueta, value=valor, width=ancho, **opciones)


def lista(etiqueta, opciones=(), ancho=280, al_elegir=None):
    return ft.Dropdown(label=etiqueta, options=list(opciones), width=ancho, on_select=al_elegir, menu_height=300)


def opcion(clave, texto):
    return ft.DropdownOption(key=str(clave), text=texto)


def tabla(*columnas):
    return ft.DataTable(columns=[ft.DataColumn(label=ft.Text(c)) for c in columnas], rows=[])


def fila_de_tabla(valores, acciones=()):
    """Arma una fila con textos y, opcionalmente, una última celda con botones."""
    celdas = [ft.DataCell(content=ft.Text("" if v is None else str(v))) for v in valores]
    if acciones:
        celdas.append(ft.DataCell(content=ft.Row(controls=list(acciones), spacing=0)))
    return ft.DataRow(cells=celdas)


def formulario(*controles):
    return ft.Row(controls=list(controles), wrap=True, spacing=12)


def subtitulo(texto):
    return ft.Text(texto, size=18, weight=ft.FontWeight.BOLD)


def texto_o_none(control):
    return (control.value or "").strip() or None


def id_elegido(control, nombre):
    """Convierte la opción elegida en el id que necesita el negocio."""
    if not control.value:
        raise ErrorNegocio(f"Debe seleccionar: {nombre}")
    return int(control.value)


def numero(control, nombre, obligatorio=True):
    texto = (control.value or "").strip().replace(",", ".")
    if not texto:
        if obligatorio:
            raise ErrorNegocio(f"{nombre}: es obligatorio")
        return None
    try:
        return float(texto)
    except ValueError:
        raise ErrorNegocio(f"{nombre}: debe ser un número") from None


class Pantalla(ABC):
    """Base de las pantallas: recogen datos, llaman al negocio y muestran el resultado.

    Las pantallas no contienen SQL ni reglas de negocio.
    """

    titulo = ""

    def __init__(self):
        self.mensaje = ft.Text()

    @abstractmethod
    def controles(self):
        """Devuelve los controles propios de la pantalla."""

    def refrescar(self):
        """Vuelve a leer las opciones y las tablas. Se ejecuta cada vez que se abre la pantalla."""

    def build(self):
        return ft.Column(
            controls=[ft.Text(self.titulo, size=26, weight=ft.FontWeight.BOLD), self.mensaje, *self.controles()],
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _informar(self, texto):
        self.mensaje.value = texto
        self.mensaje.color = ft.Colors.GREEN_800

    def _informar_error(self, texto):
        self.mensaje.value = texto
        self.mensaje.color = ft.Colors.RED_700

    def _intentar(self, accion):
        """Ejecuta una acción del usuario y muestra el error del negocio si lo hay."""
        try:
            accion()
        except ErrorNegocio as error:
            self._informar_error(str(error))
