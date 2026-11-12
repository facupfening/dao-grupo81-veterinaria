import flet as ft

from interfaz.pantalla import (Dialogo, Pantalla, boton_nuevo, campo_fecha, fila_de_tabla, formulario, id_elegido, lista,
                               opcion, subtitulo, tabla, tarjeta, vaciar)
from negocio.gestor_atencion import GestorAtencion
from negocio.gestor_catalogos import GestorCatalogos
from negocio.gestor_mascotas import GestorMascotas


class PantallaTurnos(Pantalla):
    """Muestra una tabla de turnos por cada veterinario y, debajo, las clínicas del sistema.

    El veterinario se elige recién al registrar un turno.
    """

    titulo = "Turnos y veterinarios"

    def __init__(self, ruta):
        super().__init__()
        self.gestor = GestorAtencion(ruta)
        self.mascotas = GestorMascotas(ruta)
        self.catalogos = GestorCatalogos(ruta)
        self.veterinario = lista("Veterinario *")
        self.mascota = lista("Mascota *")
        self.inicio = campo_fecha("Inicio *")
        self.fin = campo_fecha("Fin *", desde=self.inicio)
        self.tablas = {}  # Tabla de turnos de cada veterinario, por su id.
        self.agenda = ft.Column(spacing=16)
        self.tabla_clinicas = tabla("Clínica", "Dirección", "Teléfono", "Veterinarios")
        self.dialogo = Dialogo("Nuevo turno", [formulario(self.veterinario, self.mascota, self.inicio, self.fin)],
                               self.reservar, texto_boton="Reservar")

    def controles(self):
        return [
            ft.Row(controls=[boton_nuevo("Registrar turno", self.nuevo)]),
            self.agenda,
            tarjeta(
                subtitulo("Clínicas"),
                ft.Row(controls=[self.tabla_clinicas], scroll=ft.ScrollMode.AUTO),
            ),
        ]

    def refrescar(self):
        self.mascota.options = [opcion(m["id"], f"{m['nombre']} ({m['responsable']})")
                                for m in self.mascotas.listar_detallado()]
        veterinarios = self.catalogos.listar_veterinarios()
        self.veterinario.options = [opcion(v["id"], f"{v['apellido']}, {v['nombre']} ({v['clinica']})")
                                    for v in veterinarios]
        # Una tarjeta por veterinario: nombre, matrícula y clínica arriba, y sus turnos abajo.
        self.tablas = {}
        self.agenda.controls = []
        for v in veterinarios:
            self.tablas[v["id"]] = tabla("Inicio", "Fin", "Mascota", "Estado", "Acciones")
            self.agenda.controls.append(tarjeta(
                subtitulo(f"{v['apellido']}, {v['nombre']}"),
                ft.Text(f"Matrícula {v['matricula']} · {v['clinica']}", color=ft.Colors.BLUE_GREY_700),
                ft.Row(controls=[self.tablas[v["id"]]], scroll=ft.ScrollMode.AUTO),
            ))
        # Clínicas con la cantidad de veterinarios asociados, contados de la lista que ya se trajo.
        self.tabla_clinicas.rows = [
            fila_de_tabla([c["nombre"], c["direccion"], c["telefono"],
                           sum(1 for v in veterinarios if v["clinica_id"] == c["id"])])
            for c in self.catalogos.listar_clinicas()
        ]
        self._mostrar_turnos()

    def nuevo(self, e):
        vaciar(self.veterinario, self.mascota, self.inicio, self.fin)
        self._abrir_dialogo(self.dialogo)

    def reservar(self, e):
        self._intentar(self._reservar)

    def _reservar(self):
        self.gestor.reservar_turno(id_elegido(self.mascota, "Mascota"), id_elegido(self.veterinario, "Veterinario"),
                                   self.inicio.value, self.fin.value)
        self._informar("Turno reservado.")
        self._cerrar_dialogo()
        self.inicio.value = ""
        self.fin.value = ""
        self._mostrar_turnos()

    def cancelar(self, id):
        self._intentar(lambda: self._cancelar(id))

    def _cancelar(self, id):
        self.gestor.cancelar_turno(id)
        self._informar("Turno cancelado.")
        self._mostrar_turnos()

    def _mostrar_turnos(self):
        for veterinario_id, tabla_turnos in self.tablas.items():
            tabla_turnos.rows = [
                fila_de_tabla(
                    [t["inicio"], t["fin"], t["mascota"], t["estado"]],
                    # Solo un turno Reservado se puede cancelar.
                    [ft.IconButton(ft.Icons.CANCEL, tooltip="Cancelar", icon_color=ft.Colors.RED_700,
                                   on_click=lambda e, id=t["id"]: self.cancelar(id))]
                    if t["estado"] == "Reservado" else [ft.Text("-")],
                )
                for t in self.gestor.listar_turnos(veterinario_id)
            ]
