import flet as ft

from datos.base_datos import RUTA_DB
from interfaz.pantalla_clientes import PantallaClientes
from interfaz.pantalla_consultas import PantallaConsultas
from interfaz.pantalla_empaquetado import PantallaEmpaquetado
from interfaz.pantalla_envios import PantallaEnvios
from interfaz.pantalla_laboratorio import PantallaLaboratorio
from interfaz.pantalla_mascotas import PantallaMascotas
from interfaz.pantalla_reportes import PantallaReportes
from interfaz.pantalla_turnos import PantallaTurnos


class Aplicacion:
    """Ventana principal: un menú lateral y la pantalla elegida."""

    def __init__(self, ruta=RUTA_DB):
        secciones = [
            ("Clientes", ft.Icons.PEOPLE, PantallaClientes(ruta)),
            ("Mascotas", ft.Icons.PETS, PantallaMascotas(ruta)),
            ("Turnos", ft.Icons.EVENT, PantallaTurnos(ruta)),
            ("Consultas", ft.Icons.MEDICAL_SERVICES, PantallaConsultas(ruta)),
            ("Empaquetado", ft.Icons.INVENTORY_2, PantallaEmpaquetado(ruta)),
            ("Envíos", ft.Icons.LOCAL_SHIPPING, PantallaEnvios(ruta)),
            ("Laboratorio", ft.Icons.SCIENCE, PantallaLaboratorio(ruta)),
            ("Reportes", ft.Icons.BAR_CHART, PantallaReportes(ruta)),
        ]
        self.pantallas = [pantalla for _, _, pantalla in secciones]
        self.vistas = [pantalla.build() for pantalla in self.pantallas]
        self.menu = ft.NavigationRail(
            destinations=[ft.NavigationRailDestination(icon=icono, label=nombre) for nombre, icono, _ in secciones],
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            on_change=self.cambiar_seccion,
        )
        self.contenido = ft.Container(content=self.vistas[0], padding=20, expand=True)
        self.pantallas[0].refrescar()

    def cambiar_seccion(self, e):
        self.abrir(self.menu.selected_index)

    def abrir(self, indice):
        self.pantallas[indice].mensaje.value = ""
        self.pantallas[indice].refrescar()
        self.contenido.content = self.vistas[indice]

    def build(self):
        return ft.Row(
            controls=[self.menu, ft.VerticalDivider(width=1), self.contenido],
            expand=True,
        )


def iniciar(page: ft.Page):
    page.title = "Veterinaria - Red de Clínicas"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 1280
    page.window.height = 800
    page.add(Aplicacion().build())
