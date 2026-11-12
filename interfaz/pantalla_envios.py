import flet as ft

from estados.estado_remito import PRECINTO_INTACTO, PRECINTO_ROTO
from interfaz.pantalla import (PanelLateral, etiqueta_estado, NUMERO_CON_SIGNO, Dialogo, Pantalla, ahora, boton_nuevo, campo, campo_fecha, fila_de_tabla, formulario, id_elegido,
                               lista, numero, opcion, subtitulo, tabla, tarjeta, texto_o_none, vaciar)
from negocio.gestor import ErrorNegocio
from negocio.gestor_catalogos import GestorCatalogos
from negocio.gestor_envios import ARRIBO, DESPACHO, TRASPASO, GestorEnvios

ESTADOS_FINALES = ("Recibido", "Rechazado")


class PantallaEnvios(Pantalla):
    titulo = "Cadena de envío y recepción"

    def __init__(self, ruta):
        super().__init__()
        self.gestor = GestorEnvios(ruta)
        self.catalogos = GestorCatalogos(ruta)

        self.remito_evento = lista("Remito *")
        self.transportista = lista("Transportista *")
        self.tipo = lista("Evento *", [opcion(t, t) for t in (DESPACHO, TRASPASO, ARRIBO)], ancho=150)
        self.fecha_evento = campo_fecha("Fecha y hora *")
        self.ubicacion = campo("Ubicación *")
        self.temperatura = campo("Temperatura (°C) *", ancho=200, input_filter=NUMERO_CON_SIGNO)
        self.responsable = campo("Responsable *")

        self.remito_recepcion = lista("Remito *")
        self.precinto = lista("Precinto *", [opcion(p, p) for p in (PRECINTO_INTACTO, PRECINTO_ROTO)], ancho=150)
        self.fecha_recepcion = campo_fecha("Fecha y hora *")
        self.recibido_por = campo("Recibido por *")
        self.temp_llegada = campo("Temperatura de llegada (°C) *", ancho=290, input_filter=NUMERO_CON_SIGNO)
        self.observaciones = campo("Observaciones", ancho=380)

        self.tabla = tabla("Número", "Emisión", "Estado", "Muestras", "Acciones")
        self.detalle = ft.Column(spacing=4)
        self.panel = PanelLateral(self.detalle)
        self.dialogo_evento = Dialogo(
            "Nuevo evento de envío",
            [formulario(self.remito_evento, self.transportista, self.tipo, self.fecha_evento, self.ubicacion,
                        self.temperatura, self.responsable)],
            self.registrar_evento,
            texto_boton="Registrar evento",
        )
        self.dialogo_recepcion = Dialogo(
            "Nueva recepción en el laboratorio",
            [formulario(self.remito_recepcion, self.precinto, self.fecha_recepcion, self.recibido_por,
                        self.temp_llegada, self.observaciones)],
            self.registrar_recepcion,
            texto_boton="Registrar recepción",
        )

    def controles(self):
        return [
            ft.Row(controls=[
                boton_nuevo("Nuevo evento de envío", self.nuevo_evento),
                boton_nuevo("Nueva recepción", self.nueva_recepcion),
            ]),
            self.panel.junto_a(tarjeta(
                subtitulo("Remitos"),
                ft.Row(controls=[self.tabla], scroll=ft.ScrollMode.AUTO),
            )),
        ]

    def refrescar(self):
        remitos = self.gestor.listar_remitos()
        self.remito_evento.value = None
        self.remito_evento.options = [opcion(r.id, f"{r.numero} ({r.estado})") for r in remitos
                                      if r.estado not in ESTADOS_FINALES]
        self.remito_recepcion.value = None
        self.remito_recepcion.options = [opcion(r.id, r.numero) for r in remitos if r.estado == "En tránsito"]
        self.transportista.options = [opcion(t["id"], t["nombre"]) for t in self.catalogos.listar_transportistas()]
        self.fecha_evento.value = ahora()
        self.fecha_recepcion.value = ahora()
        self.tabla.rows = [
            fila_de_tabla(
                [r.numero, r.fecha_emision, etiqueta_estado(r.estado), len(r.muestras)],
                [ft.IconButton(ft.Icons.DESCRIPTION, tooltip="Ver trazabilidad", icon_color=ft.Colors.TEAL_700,
                               on_click=lambda e, id=r.id: self.ver_trazabilidad(id))],
                al_tocar=lambda e, id=r.id: self.ver_trazabilidad(id),
            )
            for r in remitos
        ]

    def nuevo_evento(self, e):
        vaciar(self.remito_evento, self.transportista, self.tipo, self.ubicacion, self.temperatura, self.responsable)
        self.fecha_evento.value = ahora()
        self._abrir_dialogo(self.dialogo_evento)

    def nueva_recepcion(self, e):
        vaciar(self.remito_recepcion, self.precinto, self.recibido_por, self.temp_llegada, self.observaciones)
        self.fecha_recepcion.value = ahora()
        self._abrir_dialogo(self.dialogo_recepcion)

    def registrar_evento(self, e):
        self._intentar(self._registrar_evento)

    def _registrar_evento(self):
        remito_id = id_elegido(self.remito_evento, "Remito")
        if not self.tipo.value:
            raise ErrorNegocio("Debe seleccionar: Evento")
        self.gestor.registrar_evento(remito_id, id_elegido(self.transportista, "Transportista"), self.tipo.value,
                                     self.fecha_evento.value, self.ubicacion.value,
                                     numero(self.temperatura, "Temperatura"), self.responsable.value)
        self._cerrar_dialogo()
        self.refrescar()
        self._informar("Evento registrado.")
        self.ver_trazabilidad(remito_id, conservar_mensaje=True)

    def registrar_recepcion(self, e):
        self._intentar(self._registrar_recepcion)

    def _registrar_recepcion(self):
        remito_id = id_elegido(self.remito_recepcion, "Remito")
        if not self.precinto.value:
            raise ErrorNegocio("Debe seleccionar: Precinto")
        estado = self.gestor.registrar_recepcion(
            remito_id, self.precinto.value, self.fecha_recepcion.value, self.recibido_por.value,
            numero(self.temp_llegada, "Temperatura de llegada"), texto_o_none(self.observaciones),
        )
        self._cerrar_dialogo()
        self.refrescar()
        if estado == "Rechazado":
            self._informar_error("Precinto roto: el remito y todas sus muestras fueron rechazados.")
        else:
            self._informar("Remito recibido.")
        self.ver_trazabilidad(remito_id, conservar_mensaje=True)

    def ver_trazabilidad(self, id, conservar_mensaje=False):
        datos = self.gestor.obtener_trazabilidad(id)
        remito = datos["remito"]
        precinto = datos["precinto"]
        lineas = [
            subtitulo(f"Trazabilidad del remito {remito.numero}"),
            ft.Text(f"Precinto: {precinto['numero']}, colocado por {precinto['colocado_por']}"),
            ft.Text("Estados: " + " > ".join(f"{r.estado} ({r.fecha_hora})" for r in remito.historial)),
        ]
        for evento in datos["eventos"]:
            lineas.append(ft.Text(
                f"{evento['fecha_hora']} - {evento['tipo']} en {evento['ubicacion']}, "
                f"{evento['temperatura']} °C, {evento['responsable']}"
            ))
        if datos["recepcion"]:
            recepcion = datos["recepcion"]
            lineas.append(ft.Text(
                f"Recepción {recepcion['fecha_hora']}: precinto {recepcion['estado_precinto']}, "
                f"{recepcion['temp_llegada']} °C, recibió {recepcion['recibido_por']}"
            ))
        for muestra in remito.muestras:
            lineas.append(ft.Row(controls=[ft.Text(f"Muestra {muestra.codigo}:"), etiqueta_estado(muestra.estado)]))
        self.detalle.controls = lineas
        self.panel.mostrar()
        if not conservar_mensaje:
            self.mensaje.value = ""
