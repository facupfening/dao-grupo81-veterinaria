import flet as ft

from interfaz.pantalla import (Dialogo, PanelLateral, Pantalla, ahora, boton_nuevo, campo, campo_fecha, fila_de_tabla, formulario,
                               id_elegido, lista, opcion, subtitulo, tabla, tarjeta, texto_o_none, vaciar)
from negocio.gestor_atencion import GestorAtencion
from negocio.gestor_laboratorio import GestorLaboratorio



class PantallaLaboratorio(Pantalla):
    titulo = "Resultados y comprobantes"

    def __init__(self, ruta):
        super().__init__()
        self.gestor = GestorLaboratorio(ruta)
        self.atencion = GestorAtencion(ruta)
        self.muestra = lista("Muestra recibida *", ancho=340)
        self.fecha_resultado = campo_fecha("Fecha y hora *")
        self.profesional = campo("Profesional *")
        self.valores = campo("Valores *", ancho=380)
        self.conclusion = campo("Conclusión", ancho=380)
        self.consulta = lista("Consulta *", ancho=420)
        self.fecha_comprobante = campo_fecha("Fecha y hora *")

        self.tabla_muestras = tabla("Código", "Análisis", "Acciones")
        self.busqueda = campo("Buscar por número o cliente", ancho=280)
        self.tabla_comprobantes = tabla("Número", "Fecha", "Cliente", "Clínica", "Total", "Acciones")
        self.titulo_detalle = subtitulo("Detalle del comprobante")
        self.tabla = tabla("Descripción", "Cantidad", "Precio unitario")
        self.total = ft.Text(weight=ft.FontWeight.BOLD)
        self.panel = PanelLateral(ft.Column(
            controls=[self.titulo_detalle, ft.Row(controls=[self.tabla], scroll=ft.ScrollMode.AUTO), self.total],
            spacing=10,
        ))

        self.dialogo_resultado = Dialogo(
            "Nuevo resultado",
            [formulario(self.muestra, self.fecha_resultado, self.profesional, self.valores, self.conclusion)],
            self.registrar_resultado,
            texto_boton="Registrar resultado",
        )
        self.dialogo_comprobante = Dialogo(
            "Nuevo comprobante",
            [formulario(self.consulta, self.fecha_comprobante)],
            self.emitir_comprobante,
            texto_boton="Emitir comprobante",
        )

    def controles(self):
        return [
            ft.Row(controls=[
                boton_nuevo("Nuevo resultado", self.nuevo_resultado),
                boton_nuevo("Nuevo comprobante", self.nuevo_comprobante),
            ]),
            tarjeta(
                subtitulo("Muestras recibidas pendientes de resultado"),
                ft.Row(controls=[self.tabla_muestras], scroll=ft.ScrollMode.AUTO),
            ),
            self.panel.junto_a(tarjeta(
                subtitulo("Comprobantes emitidos"),
                ft.Row(controls=[self.busqueda,
                                 ft.OutlinedButton("Buscar", icon=ft.Icons.SEARCH, on_click=self.buscar)]),
                ft.Row(controls=[self.tabla_comprobantes], scroll=ft.ScrollMode.AUTO),
            )),
        ]

    def refrescar(self):
        muestras = self.gestor.listar_muestras_recibidas()
        self.muestra.value = None
        self.muestra.options = [opcion(m["id"], f"{m['codigo']} - {m['analisis']}") for m in muestras]
        self.tabla_muestras.rows = [
            fila_de_tabla(
                [m["codigo"], m["analisis"]],
                [ft.IconButton(ft.Icons.SCIENCE, tooltip="Registrar resultado", icon_color=ft.Colors.TEAL_700,
                               on_click=lambda e, id=m["id"]: self.nuevo_resultado(e, id))],
            )
            for m in muestras
        ]
        self.consulta.options = [opcion(c["id"], f"{c['fecha_hora']} - {c['mascota']} ({c['tipo']})")
                                 for c in self.atencion.listar_consultas()]
        self.fecha_resultado.value = ahora()
        self.fecha_comprobante.value = ahora()
        self._mostrar_comprobantes()

    def buscar(self, e):
        self._mostrar_comprobantes()

    def nuevo_resultado(self, e, muestra_id=None):
        vaciar(self.muestra, self.profesional, self.valores, self.conclusion)
        if muestra_id:
            self.muestra.value = str(muestra_id)
        self.fecha_resultado.value = ahora()
        self._abrir_dialogo(self.dialogo_resultado)

    def nuevo_comprobante(self, e):
        vaciar(self.consulta)
        self.fecha_comprobante.value = ahora()
        self._abrir_dialogo(self.dialogo_comprobante)

    def registrar_resultado(self, e):
        self._intentar(self._registrar_resultado)

    def _registrar_resultado(self):
        self.gestor.registrar_resultado(id_elegido(self.muestra, "Muestra recibida"), self.fecha_resultado.value,
                                        self.profesional.value, self.valores.value, texto_o_none(self.conclusion))
        self._cerrar_dialogo()
        self.valores.value = ""
        self.conclusion.value = ""
        self.refrescar()
        self._informar("Resultado registrado. La muestra quedó Analizada.")

    def emitir_comprobante(self, e):
        self._intentar(self._emitir_comprobante)

    def _emitir_comprobante(self):
        resultado = self.gestor.emitir_comprobante(id_elegido(self.consulta, "Consulta"), self.fecha_comprobante.value)
        self._cerrar_dialogo()
        self._mostrar_comprobantes()
        self.ver_comprobante(resultado["comprobante_id"])
        self._informar(f"Comprobante {resultado['numero']} emitido.")

    def ver_comprobante(self, id):
        datos = self.gestor.obtener_comprobante(id)
        self.titulo_detalle.value = f"Detalle del comprobante {datos['comprobante']['numero']}"
        self.tabla.rows = [
            fila_de_tabla([d["descripcion"], d["cantidad"], f"$ {d['precio_unitario']:.2f}"])
            for d in datos["detalles"]
        ]
        self.total.value = f"Total: $ {datos['comprobante']['total']:.2f}"
        self.panel.mostrar()

    def _mostrar_comprobantes(self):
        self.tabla_comprobantes.rows = [
            fila_de_tabla(
                [c["numero"], c["fecha"], c["cliente"], c["clinica"], f"$ {c['total']:.2f}"],
                [ft.IconButton(ft.Icons.RECEIPT_LONG, tooltip="Ver detalle", icon_color=ft.Colors.TEAL_700,
                               on_click=lambda e, id=c["id"]: self.ver_comprobante(id))],
                al_tocar=lambda e, id=c["id"]: self.ver_comprobante(id),
            )
            for c in self.gestor.listar_comprobantes(self.busqueda.value)
        ]
