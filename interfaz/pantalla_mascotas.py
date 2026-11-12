import flet as ft

from interfaz.pantalla import (NUMERO_DECIMAL, Dialogo, Pantalla, ahora, boton_nuevo, campo, campo_fecha, fila_de_tabla, formulario, id_elegido,
                               lista, numero, opcion, subtitulo, tabla, tarjeta, texto_o_none, vaciar)
from negocio.gestor_atencion import GestorAtencion
from negocio.gestor_catalogos import GestorCatalogos
from negocio.gestor_clientes import GestorClientes
from negocio.gestor_mascotas import GestorMascotas

SIN_HISTORIA = "Tocá el ícono de historia clínica de una mascota para verla acá."


class PantallaMascotas(Pantalla):
    titulo = "Mascotas e historias clínicas"

    def __init__(self, ruta):
        super().__init__()
        self.gestor = GestorMascotas(ruta)
        self.clientes = GestorClientes(ruta)
        self.catalogos = GestorCatalogos(ruta)
        self.atencion = GestorAtencion(ruta)
        self.id_en_edicion = None
        self.cliente = lista("Responsable *")
        self.especie = lista("Especie *", ancho=180)
        self.nombre = campo("Nombre *")
        self.raza = campo("Raza")
        self.sexo = lista("Sexo", [opcion("Macho", "Macho"), opcion("Hembra", "Hembra")], ancho=150)
        self.fecha_nacimiento = campo_fecha("Nacimiento", con_hora=False, opcional=True)
        self.peso = campo("Peso (kg)", ancho=120, input_filter=NUMERO_DECIMAL)
        self.antecedentes = campo("Antecedentes", ancho=480)
        self.tabla = tabla("Nombre", "Especie", "Raza", "Responsable", "Acciones")
        self.detalle = ft.Column(spacing=4, controls=[ft.Text(SIN_HISTORIA)])
        self.dialogo = Dialogo(
            "Nueva mascota",
            [formulario(self.cliente, self.especie, self.nombre, self.raza, self.sexo, self.fecha_nacimiento,
                        self.peso, self.antecedentes)],
            self.guardar,
        )

    def controles(self):
        return [
            ft.Row(controls=[boton_nuevo("Nueva mascota", self.nuevo)]),
            tarjeta(
                subtitulo("Listado"),
                ft.Row(controls=[self.tabla], scroll=ft.ScrollMode.AUTO),
            ),
            tarjeta(self.detalle),
        ]

    def refrescar(self):
        self.cliente.options = [opcion(c.id, str(c)) for c in self.clientes.listar()]
        self.especie.options = [opcion(e["id"], e["nombre"]) for e in self.catalogos.listar_especies()]
        self.tabla.rows = [
            fila_de_tabla(
                [m["nombre"], m["especie"], m["raza"], m["responsable"]],
                [
                    ft.IconButton(ft.Icons.DESCRIPTION, tooltip="Ver historia clínica", icon_color=ft.Colors.TEAL_700,
                                  on_click=lambda e, id=m["id"]: self.ver_historia(id)),
                    ft.IconButton(ft.Icons.EDIT, tooltip="Editar", icon_color=ft.Colors.BLUE_700,
                                  on_click=lambda e, id=m["id"]: self.editar(id)),
                    ft.IconButton(ft.Icons.DELETE, tooltip="Dar de baja", icon_color=ft.Colors.RED_700,
                                  on_click=lambda e, id=m["id"]: self.borrar(id)),
                ],
            )
            for m in self.gestor.listar_detallado()
        ]

    def nuevo(self, e):
        self._vaciar()
        self._abrir_dialogo(self.dialogo, "Nueva mascota")

    def guardar(self, e):
        self._intentar(self._guardar)

    def _guardar(self):
        cliente_id = id_elegido(self.cliente, "Responsable")
        especie_id = id_elegido(self.especie, "Especie")
        datos = {
            "raza": texto_o_none(self.raza),
            "sexo": self.sexo.value,
            "fecha_nacimiento": texto_o_none(self.fecha_nacimiento),
            "peso_kg": numero(self.peso, "Peso", obligatorio=False),
        }
        if self.id_en_edicion:
            self.gestor.modificar(self.id_en_edicion, cliente_id, especie_id, self.nombre.value, **datos)
            self.gestor.actualizar_antecedentes(self.id_en_edicion, texto_o_none(self.antecedentes))
            self._informar("Mascota modificada.")
        else:
            self.gestor.alta(cliente_id, especie_id, self.nombre.value, ahora(),
                             antecedentes=texto_o_none(self.antecedentes), **datos)
            self._informar("Mascota registrada y historia clínica abierta.")
        self._cerrar_dialogo()
        self._vaciar()
        self.refrescar()

    def editar(self, id):
        historia = self.gestor.obtener_historia(id)["historia"]
        mascota = self.gestor.obtener(id)
        self.id_en_edicion = id
        self.cliente.value = str(mascota.cliente_id)
        self.especie.value = str(mascota.especie_id)
        self.nombre.value = mascota.nombre
        self.raza.value = mascota.raza or ""
        self.sexo.value = mascota.sexo
        self.fecha_nacimiento.value = mascota.fecha_nacimiento or ""
        self.peso.value = "" if mascota.peso_kg is None else str(mascota.peso_kg)
        self.antecedentes.value = historia["antecedentes"] or ""
        self._abrir_dialogo(self.dialogo, f"Editar mascota {mascota.nombre}")

    def borrar(self, id):
        self._intentar(lambda: self._borrar(id))

    def _borrar(self, id):
        self.gestor.baja(id)
        self.detalle.controls = [ft.Text(SIN_HISTORIA)]
        self._informar("Mascota dada de baja.")
        self.refrescar()

    def ver_historia(self, id):
        self._intentar(lambda: self._ver_historia(id))

    def _ver_historia(self, id):
        mascota = self.gestor.obtener(id)
        datos = self.gestor.obtener_historia(id)
        esquema = self.atencion.esquema_vacunas(id, ahora())
        lineas = [
            subtitulo(f"Historia clínica de {mascota.nombre}"),
            ft.Text(f"Apertura: {datos['historia']['fecha_apertura']}"),
            ft.Text(f"Antecedentes: {datos['historia']['antecedentes'] or 'sin datos'}"),
            ft.Text(f"Vacunas pendientes: {', '.join(esquema['vacunas_pendientes']) or 'ninguna'}"),
            ft.Text(f"Vacunas vencidas: {', '.join(esquema['vacunas_vencidas']) or 'ninguna'}"),
        ]
        for c in datos["consultas"]:
            lineas.append(ft.Text(
                f"{c['fecha_hora']} - {c['tipo']}: {c['diagnostico'] or 'sin diagnóstico'}; "
                f"tratamiento: {c['tratamiento'] or 'sin datos'}"
            ))
        for v in datos["vacunas"]:
            lineas.append(ft.Text(f"{v['fecha_aplicacion']} - Vacuna {v['vacuna']}; próxima: {v['fecha_proxima'] or '-'}"))
        for orden in datos["ordenes"]:
            for item in orden["muestras"]:
                muestra = item["muestra"]
                resultado = item["resultado"]
                conclusion = f"; resultado: {resultado['valores']}" if resultado else ""
                lineas.append(ft.Text(f"{orden['orden']['fecha_emision']} - Muestra {muestra.codigo}: {muestra.estado}{conclusion}"))
        self.detalle.controls = lineas

    def _vaciar(self):
        self.id_en_edicion = None
        vaciar(self.cliente, self.especie, self.nombre, self.raza, self.sexo, self.fecha_nacimiento, self.peso,
               self.antecedentes)
