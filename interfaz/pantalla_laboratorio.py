import flet as ft

from interfaz.pantalla import (Pantalla, ahora, campo, fila_de_tabla, formulario, id_elegido, lista, opcion, subtitulo,
                               tabla, texto_o_none)
from negocio.gestor_atencion import GestorAtencion
from negocio.gestor_laboratorio import GestorLaboratorio


class PantallaLaboratorio(Pantalla):
    titulo = "Resultados y comprobantes"

    def __init__(self, ruta):
        super().__init__()
        self.gestor = GestorLaboratorio(ruta)
        self.atencion = GestorAtencion(ruta)
        self.muestra = lista("Muestra recibida", ancho=340)
        self.fecha_resultado = campo("Fecha (AAAA-MM-DD HH:MM)")
        self.profesional = campo("Profesional")
        self.valores = campo("Valores", ancho=380)
        self.conclusion = campo("Conclusión", ancho=380)
        self.consulta = lista("Consulta", ancho=420)
        self.fecha_comprobante = campo("Fecha (AAAA-MM-DD HH:MM)")
        self.tabla = tabla("Descripción", "Cantidad", "Precio unitario")
        self.total = ft.Text(weight=ft.FontWeight.BOLD)

    def controles(self):
        return [
            subtitulo("Registrar resultado"),
            formulario(self.muestra, self.fecha_resultado, self.profesional, self.valores, self.conclusion),
            ft.Row(controls=[ft.Button("Registrar resultado", on_click=self.registrar_resultado)]),
            ft.Divider(),
            subtitulo("Emitir comprobante"),
            formulario(self.consulta, self.fecha_comprobante),
            ft.Row(controls=[ft.Button("Emitir comprobante", on_click=self.emitir_comprobante)]),
            ft.Row(controls=[self.tabla], scroll=ft.ScrollMode.AUTO),
            self.total,
        ]

    def refrescar(self):
        self.muestra.value = None
        self.muestra.options = [opcion(m["id"], f"{m['codigo']} - {m['analisis']}")
                                for m in self.gestor.listar_muestras_recibidas()]
        self.consulta.options = [opcion(c["id"], f"{c['fecha_hora']} - {c['mascota']} ({c['tipo']})")
                                 for c in self.atencion.listar_consultas()]
        self.fecha_resultado.value = ahora()
        self.fecha_comprobante.value = ahora()

    def registrar_resultado(self, e):
        self._intentar(self._registrar_resultado)

    def _registrar_resultado(self):
        self.gestor.registrar_resultado(id_elegido(self.muestra, "Muestra recibida"), self.fecha_resultado.value,
                                        self.profesional.value, self.valores.value, texto_o_none(self.conclusion))
        self.valores.value = ""
        self.conclusion.value = ""
        self.refrescar()
        self._informar("Resultado registrado. La muestra quedó Analizada.")

    def emitir_comprobante(self, e):
        self._intentar(self._emitir_comprobante)

    def _emitir_comprobante(self):
        resultado = self.gestor.emitir_comprobante(id_elegido(self.consulta, "Consulta"), self.fecha_comprobante.value)
        datos = self.gestor.obtener_comprobante(resultado["comprobante_id"])
        self.tabla.rows = [
            fila_de_tabla([d["descripcion"], d["cantidad"], f"$ {d['precio_unitario']:.2f}"])
            for d in datos["detalles"]
        ]
        self.total.value = f"Total: $ {resultado['total']:.2f}"
        self._informar(f"Comprobante {resultado['numero']} emitido.")
