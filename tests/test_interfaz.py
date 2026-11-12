"""Recorre las pantallas sin abrir una ventana: carga valores y ejecuta los mismos eventos que los botones."""

import flet as ft
import pytest

from datos.base_datos import conectar, inicializar
from interfaz.aplicacion import Aplicacion

CLIENTES, MASCOTAS, TURNOS, CONSULTAS, EMPAQUETADO, ENVIOS, LABORATORIO = range(7)
VERDE, ROJO = ft.Colors.GREEN_800, ft.Colors.RED_700


@pytest.fixture
def ruta(tmp_path):
    ruta = tmp_path / "prueba.db"
    inicializar(ruta)
    return ruta


@pytest.fixture
def app(ruta):
    return Aplicacion(ruta)


def abrir(app, indice):
    app.abrir(indice)
    return app.pantallas[indice]


def elegir_por_texto(control, fragmento):
    control.value = next(o.key for o in control.options if fragmento in o.text)


def registrar_consulta(pantalla, mascota="Toby", tipo="Control"):
    elegir_por_texto(pantalla.mascota, mascota)
    pantalla.elegir_mascota(None)
    elegir_por_texto(pantalla.veterinario, "Gómez")
    pantalla.tipo.value = tipo
    pantalla.fecha.value = "2026-11-03 10:00"
    pantalla.precio.value = "20000"
    pantalla.diagnostico.value = "Otitis"
    pantalla.registrar(None)


def emitir_orden(pantalla, analisis=("Hemograma completo", "Perfil bioquímico")):
    elegir_por_texto(pantalla.laboratorio, "Central")
    pantalla.responsable.value = "Laura Gómez"
    pantalla.fecha_orden.value = "2026-11-03 10:20"
    pantalla.fecha_extraccion.value = "2026-11-03 10:15"
    for nombre in analisis:
        elegir_por_texto(pantalla.analisis, nombre)
        pantalla.agregar_muestra(None)
    pantalla.emitir(None)


def empaquetar(pantalla, conservadora="REF-01"):
    for control in pantalla.muestras.controls:
        control.value = True
    elegir_por_texto(pantalla.conservadora, conservadora)
    pantalla.responsable.value = "Laura Gómez"
    pantalla.fecha.value = "2026-11-03 11:00"
    pantalla.empaquetar(None)


def registrar_evento(pantalla, tipo, fecha):
    pantalla.remito_evento.value = pantalla.remito_evento.options[0].key
    elegir_por_texto(pantalla.transportista, "Ejemplo")
    pantalla.tipo.value = tipo
    pantalla.fecha_evento.value = fecha
    pantalla.ubicacion.value = "Ruta 9"
    pantalla.temperatura.value = "5,5"
    pantalla.responsable.value = "Chofer"
    pantalla.registrar_evento(None)


def recibir(pantalla, precinto):
    pantalla.remito_recepcion.value = pantalla.remito_recepcion.options[0].key
    pantalla.precinto.value = precinto
    pantalla.fecha_recepcion.value = "2026-11-03 15:00"
    pantalla.recibido_por.value = "Bioquímica"
    pantalla.temp_llegada.value = "6"
    pantalla.registrar_recepcion(None)


def llevar_hasta_la_recepcion(app, precinto="Intacto"):
    consultas = abrir(app, CONSULTAS)
    registrar_consulta(consultas)
    emitir_orden(consultas)
    empaquetar(abrir(app, EMPAQUETADO))
    envios = abrir(app, ENVIOS)
    registrar_evento(envios, "Despacho", "2026-11-03 12:00")
    registrar_evento(envios, "Arribo", "2026-11-03 14:00")
    recibir(envios, precinto)
    return envios


def test_todas_las_pantallas_se_abren(app):
    for indice in range(len(app.pantallas)):
        abrir(app, indice)
        assert app.contenido.content is app.vistas[indice]


def test_clientes_alta_edicion_y_baja(app):
    pantalla = abrir(app, CLIENTES)
    assert len(pantalla.tabla.rows) == 3
    pantalla.dni.value = "40111222"
    pantalla.nombre.value = "Marta"
    pantalla.apellido.value = "Paz"
    pantalla.guardar(None)
    assert pantalla.mensaje.color == VERDE
    assert len(pantalla.tabla.rows) == 4
    assert pantalla.dni.value == ""

    cliente = pantalla.gestor.obtener_por_dni("40111222")
    pantalla.editar(cliente)
    pantalla.apellido.value = "Paz Díaz"
    pantalla.guardar(None)
    assert pantalla.gestor.obtener(cliente.id).apellido == "Paz Díaz"
    assert pantalla.id_en_edicion is None

    pantalla.borrar(cliente)
    assert pantalla.mensaje.color == VERDE
    assert len(pantalla.tabla.rows) == 3


def test_el_alta_se_hace_en_una_ventana_que_muestra_sus_errores(app):
    pantalla = abrir(app, CLIENTES)
    pantalla.nuevo(None)
    assert pantalla.dialogo.ventana.open
    pantalla.guardar(None)
    assert "DNI" in pantalla.dialogo.error.value
    assert pantalla.mensaje.value == ""
    assert pantalla.dialogo.ventana.open

    pantalla.dni.value = "40111222"
    pantalla.nombre.value = "Marta"
    pantalla.apellido.value = "Paz"
    pantalla.guardar(None)
    assert not pantalla.dialogo.ventana.open
    assert pantalla.mensaje.color == VERDE


def test_turno_nuevo_exige_elegir_el_veterinario(app):
    pantalla = abrir(app, TURNOS)
    pantalla.nuevo(None)
    assert not pantalla.dialogo.ventana.open
    assert pantalla.mensaje.color == ROJO
    elegir_por_texto(pantalla.veterinario, "Gómez")
    pantalla.nuevo(None)
    assert pantalla.dialogo.ventana.open


def test_las_fechas_se_eligen_con_calendario_y_reloj(app):
    turnos = abrir(app, TURNOS)
    assert turnos.inicio.read_only
    assert len(turnos.inicio.suffix_icon.controls) == 2  # calendario y reloj
    reportes = abrir(app, len(app.pantallas) - 1)
    assert reportes.desde.read_only
    assert len(reportes.desde.suffix_icon.controls) == 2  # calendario y borrar


def test_los_campos_numericos_filtran_lo_que_se_tipea(app):
    from interfaz.pantalla import NUMERO_CON_SIGNO, NUMERO_DECIMAL, SOLO_DIGITOS, TELEFONO

    clientes = app.pantallas[CLIENTES]
    assert clientes.dni.input_filter is SOLO_DIGITOS
    assert clientes.dni.max_length == 8
    assert clientes.telefono.input_filter is TELEFONO
    assert app.pantallas[MASCOTAS].peso.input_filter is NUMERO_DECIMAL
    assert app.pantallas[CONSULTAS].precio.input_filter is NUMERO_DECIMAL
    assert app.pantallas[ENVIOS].temperatura.input_filter is NUMERO_CON_SIGNO
    assert app.pantallas[ENVIOS].temp_llegada.input_filter is NUMERO_CON_SIGNO


def test_al_guardar_desde_una_ventana_se_redibuja_la_pagina(app):
    class PaginaFalsa:
        def __init__(self):
            self.actualizaciones = 0

        def update(self):
            self.actualizaciones += 1

        def show_dialog(self, dialogo):
            pass

        def pop_dialog(self):
            pass

    pagina = PaginaFalsa()
    pantalla = abrir(app, CLIENTES)
    pantalla.pagina = pagina
    pantalla.nuevo(None)
    pantalla.dni.value = "40111222"
    pantalla.nombre.value = "Marta"
    pantalla.apellido.value = "Paz"
    pantalla.guardar(None)
    assert pagina.actualizaciones == 1
    assert len(pantalla.tabla.rows) == 4


def test_los_campos_obligatorios_de_mascota_tienen_asterisco(app):
    pantalla = app.pantallas[MASCOTAS]
    for control in (pantalla.cliente, pantalla.especie, pantalla.nombre):
        assert control.label.endswith("*")
    for control in (pantalla.raza, pantalla.sexo, pantalla.fecha_nacimiento, pantalla.peso, pantalla.antecedentes):
        assert not control.label.endswith("*")


def test_el_calendario_de_hasta_no_ofrece_dias_anteriores_a_desde(app):
    from datetime import datetime
    from types import SimpleNamespace

    abiertos = []
    pagina = SimpleNamespace(show_dialog=abiertos.append)
    evento = SimpleNamespace(control=SimpleNamespace(page=pagina))

    reportes = app.pantallas[len(app.pantallas) - 1]
    reportes.desde.value = "2026-11-10"
    reportes.hasta.value = "2026-11-01"
    reportes.hasta.on_click(evento)
    calendario = abiertos[-1]
    assert calendario.first_date == datetime(2026, 11, 10)
    assert calendario.value == datetime(2026, 11, 10)

    turnos = app.pantallas[TURNOS]
    turnos.inicio.value = "2026-11-20 10:00"
    turnos.fin.on_click(evento)
    assert abiertos[-1].first_date == datetime(2026, 11, 20)


def test_una_ventana_nueva_no_muestra_lo_cargado_antes(app):
    envios = app.pantallas[ENVIOS]
    envios.precinto.value = "Roto"
    envios.recibido_por.value = "Alguien"
    envios.nueva_recepcion(None)
    assert envios.precinto.value is None
    assert envios.recibido_por.value == ""

    consultas = abrir(app, CONSULTAS)
    elegir_por_texto(consultas.analisis, "Hemograma")
    consultas.agregar_muestra(None)
    consultas.responsable.value = "Laura"
    consultas.nueva_orden(None)
    assert consultas.muestras_de_orden == []
    assert consultas.responsable.value == ""


def test_un_doble_clic_no_abre_la_ventana_dos_veces(app):
    from types import SimpleNamespace

    abiertas = []
    pantalla = abrir(app, CLIENTES)
    pantalla.pagina = SimpleNamespace(show_dialog=abiertas.append, update=lambda: None)
    pantalla.nuevo(None)
    pantalla.nuevo(None)
    assert len(abiertas) == 1


def test_las_muestras_agregadas_se_ven_en_lista_y_se_pueden_quitar(app):
    pantalla = abrir(app, CONSULTAS)
    for nombre in ("Hemograma", "Perfil"):
        elegir_por_texto(pantalla.analisis, nombre)
        pantalla.agregar_muestra(None)
    assert len(pantalla.lista_muestras.controls) == 2
    assert "Hemograma" in pantalla.lista_muestras.controls[0].controls[1].value
    pantalla.quitar_muestra(0)
    assert len(pantalla.muestras_de_orden) == 1
    assert "Perfil" in pantalla.lista_muestras.controls[0].controls[1].value


def test_clientes_muestra_los_errores_del_negocio(app):
    pantalla = abrir(app, CLIENTES)
    pantalla.dni.value = "30000001"
    pantalla.nombre.value = "Otra"
    pantalla.apellido.value = "Persona"
    pantalla.guardar(None)
    assert pantalla.mensaje.color == ROJO
    assert "Ya existe" in pantalla.mensaje.value
    assert pantalla.dni.value == "30000001"


def test_clientes_no_borra_si_tiene_mascotas(app):
    pantalla = abrir(app, CLIENTES)
    pantalla.borrar(pantalla.gestor.obtener_por_dni("30000001"))
    assert pantalla.mensaje.color == ROJO
    assert "mascotas" in pantalla.mensaje.value


def test_clientes_busca_por_apellido(app):
    pantalla = abrir(app, CLIENTES)
    pantalla.busqueda.value = "Sosa"
    pantalla.buscar(None)
    assert len(pantalla.tabla.rows) == 1


def test_mascotas_alta_edicion_e_historia(app):
    pantalla = abrir(app, MASCOTAS)
    pantalla.guardar(None)
    assert pantalla.mensaje.color == ROJO
    assert "Responsable" in pantalla.mensaje.value

    elegir_por_texto(pantalla.cliente, "López")
    elegir_por_texto(pantalla.especie, "Perro")
    pantalla.nombre.value = "Rocco"
    pantalla.peso.value = "12,5"
    pantalla.antecedentes.value = "Displasia"
    pantalla.guardar(None)
    assert pantalla.mensaje.color == VERDE
    mascota = next(m for m in pantalla.gestor.listar() if m.nombre == "Rocco")
    assert mascota.peso_kg == 12.5

    pantalla.editar(mascota.id)
    assert pantalla.antecedentes.value == "Displasia"
    pantalla.raza.value = "Beagle"
    pantalla.antecedentes.value = "Displasia leve"
    pantalla.guardar(None)
    assert pantalla.gestor.obtener(mascota.id).raza == "Beagle"
    assert pantalla.gestor.obtener_historia(mascota.id)["historia"]["antecedentes"] == "Displasia leve"

    pantalla.ver_historia(mascota.id)
    textos = [c.value for c in pantalla.detalle.controls]
    assert "Vacunas pendientes: Antirrábica, Séxtuple" in textos

    pantalla.borrar(mascota.id)
    assert pantalla.gestor.obtener(mascota.id) is None


def test_mascotas_peso_no_numerico_da_un_mensaje_claro(app):
    pantalla = abrir(app, MASCOTAS)
    elegir_por_texto(pantalla.cliente, "López")
    elegir_por_texto(pantalla.especie, "Perro")
    pantalla.nombre.value = "Rocco"
    pantalla.peso.value = "mucho"
    pantalla.guardar(None)
    assert pantalla.mensaje.value == "Peso: debe ser un número"


def test_turnos_reserva_superposicion_y_cancelacion(app):
    pantalla = abrir(app, TURNOS)
    elegir_por_texto(pantalla.mascota, "Toby")
    elegir_por_texto(pantalla.veterinario, "Gómez")
    pantalla.elegir_veterinario(None)
    pantalla.inicio.value = "2026-11-03 10:00"
    pantalla.fin.value = "2026-11-03 10:30"
    pantalla.reservar(None)
    assert pantalla.mensaje.color == VERDE
    assert len(pantalla.tabla.rows) == 1

    pantalla.inicio.value = "2026-11-03 10:15"
    pantalla.fin.value = "2026-11-03 10:45"
    pantalla.reservar(None)
    assert pantalla.mensaje.color == ROJO
    assert "ya tiene un turno" in pantalla.mensaje.value

    turno = pantalla.gestor.listar_turnos(int(pantalla.veterinario.value))[0]
    pantalla.cancelar(turno["id"])
    assert pantalla.gestor.listar_turnos(int(pantalla.veterinario.value))[0]["estado"] == "Cancelado"


def test_consulta_con_turno_y_vacuna_informa_el_esquema(app):
    turnos = abrir(app, TURNOS)
    elegir_por_texto(turnos.mascota, "Toby")
    elegir_por_texto(turnos.veterinario, "Gómez")
    turnos.inicio.value = "2026-11-03 10:00"
    turnos.fin.value = "2026-11-03 10:30"
    turnos.reservar(None)

    pantalla = abrir(app, CONSULTAS)
    elegir_por_texto(pantalla.mascota, "Toby")
    pantalla.elegir_mascota(None)
    assert len(pantalla.turno.options) == 1
    pantalla.turno.value = pantalla.turno.options[0].key
    elegir_por_texto(pantalla.vacuna, "Antirrábica")
    pantalla.lote.value = "L-1"
    pantalla.agregar_vacuna(None)
    renglon = pantalla.lista_vacunas.controls[0]
    assert "Antirrábica - lote L-1" in renglon.controls[1].value
    elegir_por_texto(pantalla.veterinario, "Gómez")
    pantalla.tipo.value = "Control"
    pantalla.fecha.value = "2026-11-03 10:05"
    pantalla.precio.value = "20000"
    pantalla.registrar(None)
    assert pantalla.mensaje.color == VERDE
    assert "Vacunas pendientes: Séxtuple" in pantalla.mensaje.value
    assert pantalla.turno.options == []
    assert pantalla.vacunas_aplicadas == []
    assert pantalla.consulta.value is not None


def test_consulta_sin_tipo_o_con_precio_invalido_no_se_registra(app):
    pantalla = abrir(app, CONSULTAS)
    registrar_consulta(pantalla, tipo=None)
    assert "Tipo" in pantalla.mensaje.value
    pantalla.tipo.value = "Control"
    pantalla.precio.value = "abc"
    pantalla.registrar(None)
    assert pantalla.mensaje.value == "Precio: debe ser un número"
    assert pantalla.gestor.listar_consultas() == []


def test_orden_sin_muestras_no_se_emite(app):
    pantalla = abrir(app, CONSULTAS)
    registrar_consulta(pantalla)
    emitir_orden(pantalla, analisis=())
    assert pantalla.mensaje.color == ROJO
    assert "al menos una muestra" in pantalla.mensaje.value


def test_orden_rechazada_conserva_las_muestras_cargadas(app):
    pantalla = abrir(app, CONSULTAS)
    registrar_consulta(pantalla)
    elegir_por_texto(pantalla.laboratorio, "Central")
    pantalla.fecha_orden.value = "2026-11-03 10:20"
    pantalla.fecha_extraccion.value = "2026-11-03 10:15"
    elegir_por_texto(pantalla.analisis, "Hemograma")
    pantalla.agregar_muestra(None)
    pantalla.responsable.value = ""
    pantalla.emitir(None)
    assert pantalla.mensaje.color == ROJO
    assert len(pantalla.muestras_de_orden) == 1


def test_empaquetado_incompatible_muestra_el_motivo(app):
    consultas = abrir(app, CONSULTAS)
    registrar_consulta(consultas)
    emitir_orden(consultas)
    pantalla = abrir(app, EMPAQUETADO)
    assert len(pantalla.muestras.controls) == 2
    empaquetar(pantalla, conservadora="AMB-01")
    assert pantalla.mensaje.color == ROJO
    assert "no es compatible" in pantalla.mensaje.value


def test_empaquetado_sin_muestras_elegidas_es_rechazado(app):
    consultas = abrir(app, CONSULTAS)
    registrar_consulta(consultas)
    emitir_orden(consultas)
    pantalla = abrir(app, EMPAQUETADO)
    elegir_por_texto(pantalla.conservadora, "REF-01")
    pantalla.responsable.value = "Laura Gómez"
    pantalla.empaquetar(None)
    assert "al menos una muestra" in pantalla.mensaje.value


def test_recorrido_completo_con_precinto_intacto(app, ruta):
    envios = llevar_hasta_la_recepcion(app)
    assert envios.mensaje.value == "Remito recibido."
    assert any("Recepción" in c.value for c in envios.detalle.controls if isinstance(c, ft.Text))
    assert envios.remito_evento.options == []

    laboratorio = abrir(app, LABORATORIO)
    assert len(laboratorio.muestra.options) == 2
    assert len(laboratorio.tabla_muestras.rows) == 2
    for valores in ("Hto 45%", "Glucosa 90"):
        laboratorio.muestra.value = laboratorio.muestra.options[0].key
        laboratorio.profesional.value = "Bioquímica"
        laboratorio.fecha_resultado.value = "2026-11-04 09:00"
        laboratorio.valores.value = valores
        laboratorio.registrar_resultado(None)
        assert laboratorio.mensaje.color == VERDE
    assert laboratorio.muestra.options == []

    laboratorio.consulta.value = laboratorio.consulta.options[0].key
    laboratorio.fecha_comprobante.value = "2026-11-04 10:00"
    laboratorio.emitir_comprobante(None)
    assert laboratorio.total.value == "Total: $ 63000.00"
    assert len(laboratorio.tabla.rows) == 3
    assert len(laboratorio.tabla_comprobantes.rows) == 1
    assert laboratorio.tabla_muestras.rows == []

    laboratorio.busqueda.value = "Sosa"
    laboratorio.buscar(None)
    assert laboratorio.tabla_comprobantes.rows == []
    laboratorio.busqueda.value = "Martínez"
    laboratorio.buscar(None)
    assert len(laboratorio.tabla_comprobantes.rows) == 1


def test_precinto_roto_rechaza_y_no_deja_cargar_resultados(app):
    envios = llevar_hasta_la_recepcion(app, "Roto")
    assert envios.mensaje.color == ROJO
    assert "rechazados" in envios.mensaje.value
    laboratorio = abrir(app, LABORATORIO)
    assert laboratorio.muestra.options == []
    laboratorio.consulta.value = laboratorio.consulta.options[0].key
    laboratorio.fecha_comprobante.value = "2026-11-04 10:00"
    laboratorio.emitir_comprobante(None)
    assert laboratorio.total.value == "Total: $ 20000.00"


def test_evento_invalido_muestra_el_error(app):
    consultas = abrir(app, CONSULTAS)
    registrar_consulta(consultas)
    emitir_orden(consultas)
    empaquetar(abrir(app, EMPAQUETADO))
    envios = abrir(app, ENVIOS)
    registrar_evento(envios, "Arribo", "2026-11-03 12:00")
    assert envios.mensaje.color == ROJO
    assert "estado Emitido" in envios.mensaje.value


def test_al_cambiar_de_seccion_se_ven_los_datos_nuevos(app):
    clientes = abrir(app, CLIENTES)
    clientes.dni.value = "40111222"
    clientes.nombre.value = "Marta"
    clientes.apellido.value = "Paz"
    clientes.guardar(None)
    mascotas = abrir(app, MASCOTAS)
    assert any("Paz" in o.text for o in mascotas.cliente.options)


def test_las_pantallas_no_usan_sql_ni_dao():
    from pathlib import Path

    for archivo in (Path(__file__).parent.parent / "interfaz").glob("*.py"):
        contenido = archivo.read_text(encoding="utf-8")
        assert "sqlite3" not in contenido
        assert "from dao" not in contenido
        assert "execute(" not in contenido


def test_la_base_queda_integra_despues_del_recorrido(app, ruta):
    llevar_hasta_la_recepcion(app)
    cx = conectar(ruta)
    assert cx.execute("PRAGMA foreign_key_check").fetchall() == []
    cx.close()
