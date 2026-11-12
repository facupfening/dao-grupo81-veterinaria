import flet as ft

from estados.estado_muestra import ESTADOS_MUESTRA
from interfaz.pantalla import (PanelLateral, COLORES_ESTADO, Pantalla, campo, etiqueta_estado, fila_de_tabla, lista, opcion,
                               subtitulo, tabla, tarjeta)
from negocio.gestor_muestras import GestorMuestras

TODOS = "Todos"

# Qué falta hacer con una muestra según su estado, y en qué pantalla.
PROXIMO_PASO = {
    "Extraída": "Empaquetarla en un remito (pantalla Empaquetado).",
    "Empaquetada": "Despachar el remito y registrar sus tramos (pantalla Envíos).",
    "En tránsito": "Registrar la recepción del remito en el laboratorio (pantalla Envíos).",
    "Recibida": "Cargar el resultado del análisis (pantalla Laboratorio).",
    "Analizada": "Ninguno: el recorrido terminó con su resultado.",
    "Rechazada": "Ninguno: se rechazó porque el precinto del remito llegó roto.",
}


class PantallaMuestras(Pantalla):
    """Muestra en qué estado está cada muestra y todo su recorrido."""

    titulo = "Trazabilidad de muestras"

    def __init__(self, ruta):
        super().__init__()
        self.gestor = GestorMuestras(ruta)
        self.resumen = ft.Row(wrap=True, spacing=10)
        self.busqueda = campo("Buscar por código o mascota", ancho=280)
        self.estado = lista("Estado", [opcion(TODOS, TODOS)] + [opcion(e, e) for e in ESTADOS_MUESTRA],
                            ancho=200, al_elegir=self.buscar)
        self.tabla = tabla("Código", "Mascota", "Análisis", "Laboratorio", "Remito", "Estado", "Acciones")
        self.detalle = ft.Column(spacing=8)
        self.panel = PanelLateral(self.detalle)

    def controles(self):
        return [
            tarjeta(subtitulo("Muestras por estado (tocá uno para filtrar)"), self.resumen),
            self.panel.junto_a(tarjeta(
                subtitulo("Muestras"),
                ft.Row(controls=[self.busqueda, self.estado,
                                 ft.OutlinedButton("Buscar", icon=ft.Icons.SEARCH, on_click=self.buscar)], wrap=True),
                ft.Row(controls=[self.tabla], scroll=ft.ScrollMode.AUTO),
            )),
        ]

    def refrescar(self):
        self.resumen.controls = [self._cuadro_resumen(estado, cantidad)
                                 for estado, cantidad in self.gestor.contar_por_estado().items()]
        self._mostrar()

    def buscar(self, e):
        self._mostrar()

    def filtrar_por(self, estado):
        self.estado.value = estado
        self._mostrar()

    def ver_trazabilidad(self, id):
        self._intentar(lambda: self._ver_trazabilidad(id))

    def _ver_trazabilidad(self, id):
        datos = self.gestor.obtener_trazabilidad(id)
        muestra = datos["muestra"]
        lineas = [
            ft.Row(controls=[subtitulo(f"Recorrido de la muestra {muestra.codigo}"), etiqueta_estado(muestra.estado)],
                   wrap=True),
            ft.Text(f"Próximo paso: {PROXIMO_PASO[muestra.estado]}", weight=ft.FontWeight.BOLD),
            ft.Text("Historial de estados (cada cambio queda registrado y no se puede modificar):", italic=True),
        ]
        for registro in muestra.historial:
            texto = f"{registro.fecha_hora} - {registro.responsable}"
            if registro.observacion:
                texto += f" ({registro.observacion})"
            lineas.append(ft.Row(controls=[etiqueta_estado(registro.estado), ft.Text(texto, expand=True)]))
        resultado = datos["resultado"]
        if resultado:
            lineas.append(ft.Text(f"Resultado: {resultado['valores']} - cargado por {resultado['profesional']} "
                                  f"el {resultado['fecha_hora']}"))
        self.detalle.controls = lineas
        self.panel.mostrar()

    def _mostrar(self):
        estado = None if self.estado.value in (None, TODOS) else self.estado.value
        self.tabla.rows = [
            fila_de_tabla(
                [m["codigo"], m["mascota"], m["analisis"], m["laboratorio"], m["remito"] or "-",
                 etiqueta_estado(m["estado"])],
                [ft.IconButton(ft.Icons.TIMELINE, tooltip="Ver recorrido", icon_color=ft.Colors.TEAL_700,
                               on_click=lambda e, id=m["id"]: self.ver_trazabilidad(id))],
                al_tocar=lambda e, id=m["id"]: self.ver_trazabilidad(id),
            )
            for m in self.gestor.listar(self.busqueda.value, estado)
        ]

    def _cuadro_resumen(self, estado, cantidad):
        """Un cuadro de color con la cantidad de muestras en ese estado; al tocarlo, filtra la tabla."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(str(cantidad), size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text(estado, color=ft.Colors.WHITE),
                ],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=COLORES_ESTADO[estado],
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=18, vertical=8),
            width=140,
            on_click=lambda e: self.filtrar_por(estado),
            tooltip=f"Ver solo las muestras en estado {estado}",
        )
