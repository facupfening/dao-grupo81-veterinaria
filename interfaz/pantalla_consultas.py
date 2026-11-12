import flet as ft

from interfaz.pantalla import (NUMERO_DECIMAL, Dialogo, Pantalla, ahora, boton_nuevo, campo, campo_fecha, fila_de_tabla,
                               formulario, id_elegido, item_de_lista, lista, numero, opcion, subtitulo, tabla, tarjeta,
                               texto_o_none, vaciar)
from negocio.gestor import ErrorNegocio
from negocio.gestor_atencion import PRIORIDADES, TIPOS_CONSULTA, GestorAtencion
from negocio.gestor_catalogos import GestorCatalogos
from negocio.gestor_mascotas import GestorMascotas


class PantallaConsultas(Pantalla):
    titulo = "Consultas y órdenes de derivación"

    def __init__(self, ruta):
        super().__init__()
        self.gestor = GestorAtencion(ruta)
        self.mascotas = GestorMascotas(ruta)
        self.catalogos = GestorCatalogos(ruta)
        self.vacunas_aplicadas = []
        self.muestras_de_orden = []

        self.mascota = lista("Mascota *", al_elegir=self.elegir_mascota)
        self.veterinario = lista("Veterinario *")
        self.turno = lista("Turno (opcional)")
        self.tipo = lista("Tipo *", [opcion(t, t) for t in TIPOS_CONSULTA], ancho=160)
        self.fecha = campo_fecha("Fecha y hora *")
        self.precio = campo("Precio *", ancho=130, input_filter=NUMERO_DECIMAL)
        self.motivo = campo("Motivo", ancho=380)
        self.diagnostico = campo("Diagnóstico", ancho=380)
        self.tratamiento = campo("Tratamiento", ancho=380)
        self.vacuna = lista("Vacuna aplicada", ancho=240)
        self.lote = campo("Lote", ancho=130)
        self.lista_vacunas = ft.Column(spacing=0)

        self.consulta = lista("Consulta *", ancho=420)
        self.laboratorio = lista("Laboratorio *")
        self.prioridad = lista("Prioridad", [opcion(p, p) for p in PRIORIDADES], ancho=150)
        self.responsable = campo("Responsable *")
        self.fecha_orden = campo_fecha("Fecha y hora *")
        self.observaciones = campo("Observaciones", ancho=380)
        self.analisis = lista("Tipo de análisis *", ancho=280)
        self.fecha_extraccion = campo_fecha("Extracción *")
        self.lista_muestras = ft.Column(spacing=0)

        self.tabla = tabla("Fecha", "Mascota", "Tipo", "Diagnóstico", "Precio", "Acciones")
        self.dialogo_consulta = Dialogo(
            "Nueva consulta",
            [
                formulario(self.mascota, self.veterinario, self.turno, self.tipo, self.fecha, self.precio,
                           self.motivo, self.diagnostico, self.tratamiento),
                formulario(self.vacuna, self.lote, ft.OutlinedButton("Agregar vacuna", icon=ft.Icons.ADD,
                                                                     on_click=self.agregar_vacuna)),
                subtitulo("Vacunas agregadas"),
                self.lista_vacunas,
            ],
            self.registrar,
            texto_boton="Registrar consulta",
        )
        self.dialogo_orden = Dialogo(
            "Nueva orden de derivación",
            [
                formulario(self.consulta, self.laboratorio, self.prioridad, self.responsable, self.fecha_orden,
                           self.observaciones),
                formulario(self.analisis, self.fecha_extraccion,
                           ft.OutlinedButton("Agregar muestra", icon=ft.Icons.ADD, on_click=self.agregar_muestra)),
                subtitulo("Muestras agregadas"),
                self.lista_muestras,
            ],
            self.emitir,
            texto_boton="Emitir orden",
        )
        self._mostrar_vacunas()
        self._mostrar_muestras()

    def controles(self):
        return [
            ft.Row(controls=[
                boton_nuevo("Nueva consulta", self.nueva_consulta),
                boton_nuevo("Nueva orden de derivación", self.nueva_orden),
            ]),
            tarjeta(
                subtitulo("Consultas registradas"),
                ft.Row(controls=[self.tabla], scroll=ft.ScrollMode.AUTO),
            ),
        ]

    def refrescar(self):
        self.mascota.options = [opcion(m["id"], f"{m['nombre']} ({m['responsable']})")
                                for m in self.mascotas.listar_detallado()]
        self.veterinario.options = [opcion(v["id"], f"{v['apellido']}, {v['nombre']}")
                                    for v in self.catalogos.listar_veterinarios()]
        self.laboratorio.options = [opcion(l["id"], l["nombre"]) for l in self.catalogos.listar_laboratorios()]
        self.analisis.options = [opcion(t["id"], t["nombre"]) for t in self.catalogos.listar_tipos_analisis()]
        self._cargar_consultas()
        self._cargar_opciones_de_mascota()
        self.fecha.value = ahora()
        self.fecha_orden.value = ahora()
        self.fecha_extraccion.value = ahora()

    def nueva_consulta(self, e):
        # La ventana arranca vacía: no muestra lo cargado en una consulta anterior.
        vaciar(self.mascota, self.veterinario, self.turno, self.tipo, self.precio, self.motivo, self.diagnostico,
               self.tratamiento, self.vacuna, self.lote)
        self.vacunas_aplicadas = []
        self._mostrar_vacunas()
        self._cargar_opciones_de_mascota()
        self.fecha.value = ahora()
        self._abrir_dialogo(self.dialogo_consulta)

    def nueva_orden(self, e, consulta_id=None):
        vaciar(self.consulta, self.laboratorio, self.prioridad, self.responsable, self.observaciones, self.analisis)
        self.muestras_de_orden = []
        self._mostrar_muestras()
        if consulta_id:
            self.consulta.value = str(consulta_id)
        self.fecha_orden.value = ahora()
        self.fecha_extraccion.value = ahora()
        self._abrir_dialogo(self.dialogo_orden)

    def elegir_mascota(self, e):
        self.vacunas_aplicadas = []
        self._mostrar_vacunas()
        vaciar(self.turno, self.vacuna)
        self._cargar_opciones_de_mascota()

    def agregar_vacuna(self, e):
        self._intentar(self._agregar_vacuna)

    def _agregar_vacuna(self):
        vacuna_id = id_elegido(self.vacuna, "Vacuna aplicada")
        self.vacunas_aplicadas.append((vacuna_id, texto_o_none(self.lote)))
        self._mostrar_vacunas()
        vaciar(self.vacuna, self.lote)

    def quitar_vacuna(self, posicion):
        self.vacunas_aplicadas.pop(posicion)
        self._mostrar_vacunas()

    def _mostrar_vacunas(self):
        nombres = {o.key: o.text for o in self.vacuna.options}
        self.lista_vacunas.controls = [
            item_de_lista(f"{nombres.get(str(id), 'Vacuna')} - lote {lote or 'sin dato'}",
                          lambda e, i=i: self.quitar_vacuna(i))
            for i, (id, lote) in enumerate(self.vacunas_aplicadas)
        ] or [ft.Text("Todavía no agregaste vacunas.", italic=True)]

    def registrar(self, e):
        self._intentar(self._registrar)

    def _registrar(self):
        if not self.tipo.value:
            raise ErrorNegocio("Debe seleccionar: Tipo")
        resultado = self.gestor.registrar_consulta(
            id_elegido(self.mascota, "Mascota"), id_elegido(self.veterinario, "Veterinario"), self.fecha.value,
            self.tipo.value, numero(self.precio, "Precio"), texto_o_none(self.motivo), texto_o_none(self.diagnostico),
            texto_o_none(self.tratamiento), int(self.turno.value) if self.turno.value else None, self.vacunas_aplicadas,
        )
        pendientes = ", ".join(resultado["vacunas_pendientes"]) or "ninguna"
        vencidas = ", ".join(resultado["vacunas_vencidas"]) or "ninguna"
        self._informar(f"Consulta registrada. Vacunas pendientes: {pendientes}. Vencidas: {vencidas}.")
        self._cerrar_dialogo()
        self.vacunas_aplicadas = []
        self._mostrar_vacunas()
        vaciar(self.precio, self.motivo, self.diagnostico, self.tratamiento, self.turno)
        self.fecha.value = ahora()
        self._cargar_opciones_de_mascota()
        self._cargar_consultas()
        self.consulta.value = str(resultado["consulta_id"])

    def agregar_muestra(self, e):
        self._intentar(self._agregar_muestra)

    def _agregar_muestra(self):
        tipo_id = id_elegido(self.analisis, "Tipo de análisis")
        self.muestras_de_orden.append((tipo_id, self.fecha_extraccion.value))
        self._mostrar_muestras()
        vaciar(self.analisis)

    def quitar_muestra(self, posicion):
        self.muestras_de_orden.pop(posicion)
        self._mostrar_muestras()

    def _mostrar_muestras(self):
        nombres = {o.key: o.text for o in self.analisis.options}
        self.lista_muestras.controls = [
            item_de_lista(f"{nombres.get(str(id), 'Análisis')} - extracción {fecha}",
                          lambda e, i=i: self.quitar_muestra(i))
            for i, (id, fecha) in enumerate(self.muestras_de_orden)
        ] or [ft.Text("Todavía no agregaste muestras.", italic=True)]

    def emitir(self, e):
        self._intentar(self._emitir)

    def _emitir(self):
        resultado = self.gestor.emitir_orden(
            id_elegido(self.consulta, "Consulta"), id_elegido(self.laboratorio, "Laboratorio"), self.fecha_orden.value,
            self.muestras_de_orden, self.responsable.value, self.prioridad.value or "Normal",
            texto_o_none(self.observaciones),
        )
        self._informar(f"Orden emitida. Muestras: {', '.join(resultado['codigos'])}.")
        self._cerrar_dialogo()
        self.muestras_de_orden = []
        self._mostrar_muestras()
        vaciar(self.observaciones)

    def _cargar_consultas(self):
        consultas = self.gestor.listar_consultas()
        self.consulta.options = [opcion(c["id"], f"{c['fecha_hora']} - {c['mascota']} ({c['tipo']})")
                                 for c in consultas]
        self.tabla.rows = [
            fila_de_tabla(
                [c["fecha_hora"], c["mascota"], c["tipo"], c["diagnostico"], f"$ {c['precio']:.2f}"],
                [ft.IconButton(ft.Icons.SCIENCE, tooltip="Emitir orden de derivación", icon_color=ft.Colors.TEAL_700,
                               on_click=lambda e, id=c["id"]: self.nueva_orden(e, id))],
            )
            for c in consultas
        ]

    def _cargar_opciones_de_mascota(self):
        if not self.mascota.value:
            self.turno.options = []
            self.vacuna.options = []
            return
        mascota = self.mascotas.obtener(int(self.mascota.value))
        self.turno.options = [opcion(t["id"], t["inicio"]) for t in self.gestor.listar_turnos_reservados(mascota.id)]
        self.vacuna.options = [opcion(v["id"], v["nombre"])
                               for v in self.catalogos.listar_vacunas_por_especie(mascota.especie_id)]
