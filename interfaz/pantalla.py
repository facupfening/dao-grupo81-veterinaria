from abc import ABC, abstractmethod
from datetime import datetime

import flet as ft

from modelos.validaciones import FORMATO_FECHA, FORMATO_FECHA_HORA
from negocio.gestor import ErrorNegocio

# Colores de toda la aplicación, en un solo lugar para cambiarlos fácilmente.
COLOR_PRINCIPAL = ft.Colors.TEAL_700
COLOR_SUAVE = ft.Colors.TEAL_50
COLOR_FONDO = ft.Colors.BLUE_GREY_50
COLOR_TARJETA = ft.Colors.WHITE
COLOR_EXITO = ft.Colors.GREEN_800
COLOR_ERROR = ft.Colors.RED_700

# Un color por estado de muestra y de remito, para reconocerlos de un vistazo en todas las pantallas.
COLORES_ESTADO = {
    "Extraída": ft.Colors.BLUE_GREY_400,
    "Emitido": ft.Colors.BLUE_GREY_400,
    "Empaquetada": ft.Colors.INDIGO_400,
    "Despachado": ft.Colors.INDIGO_400,
    "En tránsito": ft.Colors.ORANGE_700,
    "Recibida": ft.Colors.PURPLE_400,
    "Recibido": ft.Colors.PURPLE_400,
    "Analizada": ft.Colors.GREEN_700,
    "Rechazada": ft.Colors.RED_700,
    "Rechazado": ft.Colors.RED_700,
}

# Filtros de tipeo: el campo no deja escribir lo que no corresponde.
# Igual se valida al guardar, como segunda barrera.
SOLO_DIGITOS = ft.NumbersOnlyInputFilter()
NUMERO_DECIMAL = ft.InputFilter(regex_string=r"^[0-9]*[.,]?[0-9]*$", allow=True, replacement_string="")
NUMERO_CON_SIGNO = ft.InputFilter(regex_string=r"^-?[0-9]*[.,]?[0-9]*$", allow=True, replacement_string="")
TELEFONO = ft.InputFilter(regex_string=r"^[0-9 +\-]*$", allow=True, replacement_string="")


def ahora():
    return datetime.now().strftime(FORMATO_FECHA_HORA)


def campo(etiqueta, valor="", ancho=230, **opciones):
    return ft.TextField(label=etiqueta, value=valor, width=ancho, **opciones)


PRIMER_DIA = datetime(2000, 1, 1)  # Fecha más antigua que ofrecen los calendarios.


def campo_fecha(etiqueta, con_hora=True, opcional=False, ancho=270, desde=None):
    """Campo que no se escribe: la fecha se elige con un calendario y la hora con un reloj.

    El campo guarda el texto con el formato de siempre (AAAA-MM-DD o AAAA-MM-DD HH:MM),
    así el negocio y sus validaciones no cambian.
    Si se indica `desde` (otro campo de fecha), el calendario no deja elegir días anteriores a ese campo.
    """
    texto = ft.TextField(label=etiqueta, width=ancho, read_only=True)
    calendario = ft.DatePicker(first_date=PRIMER_DIA, last_date=datetime(2100, 12, 31),
                               help_text=etiqueta, cancel_text="Cancelar", confirm_text="Aceptar")
    reloj = ft.TimePicker(help_text=etiqueta, cancel_text="Cancelar", confirm_text="Aceptar")

    def abrir_calendario(e):
        # Primer día que se puede elegir: el del campo "desde", si ya tiene fecha.
        primer_dia = PRIMER_DIA
        if desde is not None and desde.value:
            primer_dia = datetime.strptime(desde.value[:10], FORMATO_FECHA)
        calendario.first_date = primer_dia
        # El calendario arranca en la fecha del campo (o en la de hoy), pero nunca antes del primer día permitido.
        if texto.value:
            inicial = datetime.strptime(texto.value[:10], FORMATO_FECHA)
        else:
            inicial = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        calendario.value = max(inicial, primer_dia)
        e.control.page.show_dialog(calendario)

    def abrir_reloj(e):
        # El reloj arranca en la hora que ya tiene el campo, o en la actual.
        if texto.value and len(texto.value) == 16:
            reloj.value = datetime.strptime(texto.value[11:], "%H:%M").time()
        e.control.page.show_dialog(reloj)

    def al_elegir_fecha(e):
        fecha = calendario.value.strftime(FORMATO_FECHA)
        if con_hora:
            # Conserva la hora que ya tenía el campo; si no tenía, pone la actual.
            hora = texto.value[11:] if texto.value and len(texto.value) == 16 else datetime.now().strftime("%H:%M")
            fecha = f"{fecha} {hora}"
        texto.value = fecha

    def al_elegir_hora(e):
        # Conserva la fecha que ya tenía el campo; si no tenía, pone la de hoy.
        fecha = texto.value[:10] if texto.value else datetime.now().strftime(FORMATO_FECHA)
        texto.value = f"{fecha} {reloj.value.strftime('%H:%M')}"

    def borrar(e):
        texto.value = ""

    calendario.on_change = al_elegir_fecha
    reloj.on_change = al_elegir_hora
    texto.on_click = abrir_calendario
    botones = [ft.IconButton(ft.Icons.CALENDAR_MONTH, tooltip="Elegir fecha", icon_color=COLOR_PRINCIPAL,
                             on_click=abrir_calendario)]
    if con_hora:
        botones.append(ft.IconButton(ft.Icons.ACCESS_TIME, tooltip="Elegir hora", icon_color=COLOR_PRINCIPAL,
                                     on_click=abrir_reloj))
    if opcional:
        botones.append(ft.IconButton(ft.Icons.CLEAR, tooltip="Borrar", on_click=borrar))
    texto.suffix_icon = ft.Row(controls=botones, tight=True, spacing=0)
    return texto


def lista(etiqueta, opciones=(), ancho=280, al_elegir=None):
    return ft.Dropdown(label=etiqueta, options=list(opciones), width=ancho, on_select=al_elegir, menu_height=300)


def opcion(clave, texto):
    return ft.DropdownOption(key=str(clave), text=texto)


def tabla(*columnas):
    return ft.DataTable(
        columns=[ft.DataColumn(label=ft.Text(c, weight=ft.FontWeight.BOLD, color=COLOR_PRINCIPAL)) for c in columnas],
        rows=[],
        heading_row_color=COLOR_SUAVE,
        border_radius=8,
    )


def fila_de_tabla(valores, acciones=(), al_tocar=None):
    """Arma una fila con textos y, opcionalmente, una última celda con botones.

    Un valor que ya es un control (por ejemplo, una etiqueta de estado) se muestra tal cual.
    Si se indica `al_tocar`, tocar cualquier parte de la fila ejecuta esa acción.
    """
    celdas = [ft.DataCell(content=v if isinstance(v, ft.Control) else ft.Text("" if v is None else str(v)))
              for v in valores]
    if acciones:
        celdas.append(ft.DataCell(content=ft.Row(controls=list(acciones), spacing=0)))
    return ft.DataRow(cells=celdas, on_select_change=al_tocar)


def etiqueta_estado(estado, texto=None):
    """El nombre del estado sobre su color: así se ve en qué etapa está una muestra o un remito."""
    return ft.Container(
        content=ft.Text(texto or estado, color=ft.Colors.WHITE, size=12, weight=ft.FontWeight.BOLD),
        bgcolor=COLORES_ESTADO.get(estado, ft.Colors.GREY_600),
        border_radius=12,
        padding=ft.Padding.symmetric(horizontal=10, vertical=3),
    )


def formulario(*controles):
    return ft.Row(controls=list(controles), wrap=True, spacing=12)


def subtitulo(texto):
    return ft.Text(texto, size=18, weight=ft.FontWeight.BOLD, color=COLOR_PRINCIPAL)


def tarjeta(*controles):
    """Recuadro blanco con bordes redondeados que agrupa una parte de la pantalla."""
    return ft.Container(
        content=ft.Column(controls=list(controles), spacing=10),
        bgcolor=COLOR_TARJETA,
        border_radius=12,
        padding=16,
        shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.BLACK_12),
    )


def boton_nuevo(texto, al_hacer_clic):
    """Botón que abre la ventana para crear algo nuevo."""
    return ft.FilledButton(texto, icon=ft.Icons.ADD, on_click=al_hacer_clic, bgcolor=COLOR_PRINCIPAL)


def vaciar(*controles):
    """Deja los campos en blanco, para que una ventana nueva no muestre lo cargado antes."""
    for control in controles:
        if isinstance(control, ft.Dropdown):
            control.value = None
            control.text = ""  # Sin esto, el desplegable puede seguir mostrando la opción anterior.
        else:
            control.value = ""


def item_de_lista(texto, al_quitar):
    """Un renglón de una lista de elementos agregados, con un botón para quitarlo."""
    return ft.Row(
        controls=[
            ft.Icon(ft.Icons.CHECK_CIRCLE, color=COLOR_PRINCIPAL, size=18),
            ft.Text(texto, expand=True),
            ft.IconButton(ft.Icons.DELETE, tooltip="Quitar", icon_color=COLOR_ERROR, on_click=al_quitar),
        ],
    )


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


class PanelLateral:
    """Tarjeta de detalle que aparece a la derecha del listado y se cierra con la X.

    Se usa para la trazabilidad: el listado sigue visible mientras se mira el detalle.
    """

    def __init__(self, contenido):
        self.tarjeta = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(controls=[ft.IconButton(ft.Icons.CLOSE, tooltip="Cerrar", on_click=self.cerrar)],
                           alignment=ft.MainAxisAlignment.END),
                    contenido,
                ],
                spacing=0,
            ),
            bgcolor=COLOR_TARJETA,
            border_radius=12,
            padding=16,
            shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.BLACK_12),
            expand=2,
            visible=False,
        )

    def mostrar(self):
        self.tarjeta.visible = True

    def cerrar(self, e=None):
        self.tarjeta.visible = False

    def junto_a(self, *principal):
        """Pone el contenido principal a la izquierda y el panel a la derecha."""
        return ft.Row(
            controls=[ft.Column(controls=list(principal), spacing=14, expand=3), self.tarjeta],
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=14,
        )


class Dialogo:
    """Ventana emergente con el formulario para crear o editar algo.

    Tiene su propio texto de error, así el usuario ve el problema sin cerrar la ventana.
    """

    def __init__(self, titulo, controles, al_aceptar, texto_boton="Guardar"):
        self.titulo = ft.Text(titulo, color=COLOR_PRINCIPAL, weight=ft.FontWeight.BOLD)
        self.error = ft.Text(color=COLOR_ERROR)
        self.pagina = None
        self.ventana = ft.AlertDialog(
            modal=True,
            scrollable=True,
            title=self.titulo,
            content=ft.Column(
                controls=[*controles, ft.Text("* Obligatorio", size=12, italic=True), self.error],
                tight=True,
                width=600,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=self.cerrar),
                ft.FilledButton(texto_boton, icon=ft.Icons.CHECK, on_click=al_aceptar, bgcolor=COLOR_PRINCIPAL),
            ],
        )

    def abrir(self, pagina, titulo=None):
        if self.ventana.open:
            return  # Un doble clic en el botón no debe abrirla dos veces.
        if titulo:
            self.titulo.value = titulo
        self.error.value = ""
        self.pagina = pagina
        self.ventana.open = True
        # En los tests no hay página: la ventana queda marcada como abierta, sin dibujarse.
        if pagina:
            pagina.show_dialog(self.ventana)

    def cerrar(self, e=None):
        if self.ventana.open and self.pagina:
            self.pagina.pop_dialog()
        self.ventana.open = False


class Pantalla(ABC):
    """Base de las pantallas: recogen datos, llaman al negocio y muestran el resultado.

    Las pantallas no contienen SQL ni reglas de negocio.
    """

    titulo = ""

    def __init__(self):
        self.mensaje = ft.Text(weight=ft.FontWeight.BOLD)
        self.pagina = None  # La asigna Aplicacion; hace falta para mostrar las ventanas emergentes.
        self.dialogo_abierto = None

    @abstractmethod
    def controles(self):
        """Devuelve los controles propios de la pantalla."""

    def refrescar(self):
        """Vuelve a leer las opciones y las tablas. Se ejecuta cada vez que se abre la pantalla."""

    def build(self):
        return ft.Column(
            controls=[
                ft.Text(self.titulo, size=26, weight=ft.FontWeight.BOLD, color=COLOR_PRINCIPAL),
                self.mensaje,
                *self.controles(),
            ],
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _abrir_dialogo(self, dialogo, titulo=None):
        self.mensaje.value = ""
        self.dialogo_abierto = dialogo
        dialogo.abrir(self.pagina, titulo)

    def _cerrar_dialogo(self):
        if self.dialogo_abierto:
            self.dialogo_abierto.cerrar()
            self.dialogo_abierto = None

    def _informar(self, texto):
        self.mensaje.value = texto
        self.mensaje.color = COLOR_EXITO

    def _informar_error(self, texto):
        # El error se muestra donde está mirando el usuario: en la ventana abierta o en la pantalla.
        if self.dialogo_abierto and self.dialogo_abierto.ventana.open:
            self.dialogo_abierto.error.value = texto
        else:
            self.mensaje.value = texto
            self.mensaje.color = COLOR_ERROR

    def _intentar(self, accion):
        """Ejecuta una acción del usuario y muestra el error del negocio si lo hay."""
        try:
            accion()
        except ErrorNegocio as error:
            self._informar_error(str(error))
        # Flet solo redibuja la ventana donde se hizo clic. Se redibuja toda la página
        # para que la tabla de atrás muestre enseguida el registro nuevo.
        if self.pagina:
            self.pagina.update()
