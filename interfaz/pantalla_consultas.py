import flet as ft

from interfaz.pantalla import (Pantalla, ahora, campo, formulario, id_elegido, lista, numero, opcion, subtitulo,
                               texto_o_none)
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

        self.mascota = lista("Mascota", al_elegir=self.elegir_mascota)
        self.veterinario = lista("Veterinario")
        self.turno = lista("Turno (opcional)")
        self.tipo = lista("Tipo", [opcion(t, t) for t in TIPOS_CONSULTA], ancho=160)
        self.fecha = campo("Fecha (AAAA-MM-DD HH:MM)")
        self.precio = campo("Precio", ancho=130)
        self.motivo = campo("Motivo", ancho=380)
        self.diagnostico = campo("Diagnóstico", ancho=380)
        self.tratamiento = campo("Tratamiento", ancho=380)
        self.vacuna = lista("Vacuna aplicada", ancho=240)
        self.lote = campo("Lote", ancho=130)
        self.lista_vacunas = ft.Text()

        self.consulta = lista("Consulta", ancho=420)
        self.laboratorio = lista("Laboratorio")
        self.prioridad = lista("Prioridad", [opcion(p, p) for p in PRIORIDADES], ancho=150)
        self.responsable = campo("Responsable")
        self.fecha_orden = campo("Fecha (AAAA-MM-DD HH:MM)")
        self.observaciones = campo("Observaciones", ancho=380)
        self.analisis = lista("Tipo de análisis", ancho=280)
        self.fecha_extraccion = campo("Extracción (AAAA-MM-DD HH:MM)", ancho=260)
        self.lista_muestras = ft.Text()

    def controles(self):
        return [
            subtitulo("Registrar atención"),
            formulario(self.mascota, self.veterinario, self.turno, self.tipo, self.fecha, self.precio,
                       self.motivo, self.diagnostico, self.tratamiento),
            formulario(self.vacuna, self.lote, ft.OutlinedButton("Agregar vacuna", on_click=self.agregar_vacuna)),
            self.lista_vacunas,
            ft.Row(controls=[ft.Button("Registrar consulta", on_click=self.registrar)]),
            ft.Divider(),
            subtitulo("Emitir orden de derivación"),
            formulario(self.consulta, self.laboratorio, self.prioridad, self.responsable, self.fecha_orden,
                       self.observaciones),
            formulario(self.analisis, self.fecha_extraccion,
                       ft.OutlinedButton("Agregar muestra", on_click=self.agregar_muestra)),
            self.lista_muestras,
            ft.Row(controls=[ft.Button("Emitir orden", on_click=self.emitir)]),
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

    def elegir_mascota(self, e):
        self.vacunas_aplicadas = []
        self.lista_vacunas.value = ""
        self.turno.value = None
        self.vacuna.value = None
        self._cargar_opciones_de_mascota()

    def agregar_vacuna(self, e):
        self._intentar(self._agregar_vacuna)

    def _agregar_vacuna(self):
        vacuna_id = id_elegido(self.vacuna, "Vacuna aplicada")
        self.vacunas_aplicadas.append((vacuna_id, texto_o_none(self.lote)))
        nombres = {o.key: o.text for o in self.vacuna.options}
        self.lista_vacunas.value = "Vacunas a registrar: " + ", ".join(
            nombres[str(id)] for id, _ in self.vacunas_aplicadas
        )
        self.lote.value = ""

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
        self.vacunas_aplicadas = []
        self.lista_vacunas.value = ""
        for control in (self.precio, self.motivo, self.diagnostico, self.tratamiento):
            control.value = ""
        self.turno.value = None
        self.fecha.value = ahora()
        self._cargar_opciones_de_mascota()
        self._cargar_consultas()
        self.consulta.value = str(resultado["consulta_id"])

    def agregar_muestra(self, e):
        self._intentar(self._agregar_muestra)

    def _agregar_muestra(self):
        tipo_id = id_elegido(self.analisis, "Tipo de análisis")
        self.muestras_de_orden.append((tipo_id, self.fecha_extraccion.value))
        nombres = {o.key: o.text for o in self.analisis.options}
        self.lista_muestras.value = "Muestras de la orden: " + ", ".join(
            nombres[str(id)] for id, _ in self.muestras_de_orden
        )

    def emitir(self, e):
        self._intentar(self._emitir)

    def _emitir(self):
        resultado = self.gestor.emitir_orden(
            id_elegido(self.consulta, "Consulta"), id_elegido(self.laboratorio, "Laboratorio"), self.fecha_orden.value,
            self.muestras_de_orden, self.responsable.value, self.prioridad.value or "Normal",
            texto_o_none(self.observaciones),
        )
        self._informar(f"Orden emitida. Muestras: {', '.join(resultado['codigos'])}.")
        self.muestras_de_orden = []
        self.lista_muestras.value = ""
        self.observaciones.value = ""

    def _cargar_consultas(self):
        self.consulta.options = [opcion(c["id"], f"{c['fecha_hora']} - {c['mascota']} ({c['tipo']})")
                                 for c in self.gestor.listar_consultas()]

    def _cargar_opciones_de_mascota(self):
        if not self.mascota.value:
            self.turno.options = []
            self.vacuna.options = []
            return
        mascota = self.mascotas.obtener(int(self.mascota.value))
        self.turno.options = [opcion(t["id"], t["inicio"]) for t in self.gestor.listar_turnos_reservados(mascota.id)]
        self.vacuna.options = [opcion(v["id"], v["nombre"])
                               for v in self.catalogos.listar_vacunas_por_especie(mascota.especie_id)]
