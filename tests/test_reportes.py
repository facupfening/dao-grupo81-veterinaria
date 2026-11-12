import pytest
from openpyxl import load_workbook

from datos.base_datos import conectar, inicializar
from interfaz.aplicacion import Aplicacion
from negocio.datos_demo import CargaDemo
from negocio.gestor import ErrorNegocio
from negocio.gestor_atencion import GestorAtencion
from negocio.gestor_envios import GestorEnvios
from negocio.gestor_laboratorio import GestorLaboratorio
from negocio.gestor_reportes import (ATENCIONES, FACTURACION, FORMATOS, NOMBRES_REPORTES, RECHAZOS, TIEMPOS,
                                     TRATAMIENTOS, GestorReportes)
from reportes.documentos import DocumentoExcel, DocumentoMarkdown, DocumentoPDF
from reportes.exportadores import EXPORTADORES, Exportador
from reportes.reporte import Reporte

CENTRO, NORTE, SUR = "Clínica Centro", "Clínica Norte", "Clínica Sur"
TOBY, LUNA, SIMON = 1, 3, 4
GOMEZ, RIOS = 1, 3
HEMOGRAMA, BIOQUIMICO = 1, 2
TRANSPORTE_1, TRANSPORTE_2 = 1, 2
NOMBRE_1, NOMBRE_2 = "Transporte Ejemplo", "Logística Ficticia"


@pytest.fixture
def ruta(tmp_path):
    ruta = tmp_path / "prueba.db"
    inicializar(ruta)
    return ruta


def consulta(ruta, mascota=TOBY, veterinario=GOMEZ, fecha="2026-10-05 10:00", tipo="Consulta", precio=20000,
             tratamiento=None):
    return GestorAtencion(ruta).registrar_consulta(mascota, veterinario, fecha, tipo, precio,
                                                   tratamiento=tratamiento)["consulta_id"]


def derivar(ruta, consulta_id, tipos=(HEMOGRAMA,), transportistas=(TRANSPORTE_1,), precinto="Intacto",
            dia="2026-10-05", despacho="12:00", recepcion="15:00"):
    """Lleva las muestras hasta la recepción y devuelve sus ids y el remito."""
    envios = GestorEnvios(ruta)
    codigos = GestorAtencion(ruta).emitir_orden(
        consulta_id, 1, f"{dia} 10:20", [(tipo, f"{dia} 10:15") for tipo in tipos], "Laura"
    )["codigos"]
    muestras = [m["id"] for m in envios.listar_muestras_para_empaquetar() if m["codigo"] in codigos]
    remito = envios.empaquetar(muestras, 1, f"{dia} 11:00", "Laura")["remito_id"]
    envios.registrar_evento(remito, transportistas[0], "Despacho", f"{dia} {despacho}", "Clínica", 5, "Chofer")
    for transportista in transportistas[1:]:
        envios.registrar_evento(remito, transportista, "Traspaso", f"{dia} {despacho}", "Depósito", 5, "Relevo")
    envios.registrar_evento(remito, transportistas[-1], "Arribo", f"{dia} {recepcion}", "Laboratorio", 5, "Chofer")
    envios.registrar_recepcion(remito, precinto, f"{dia} {recepcion}", "Bioquímica", 5)
    return muestras, remito


def analizar(ruta, muestra, fecha):
    GestorLaboratorio(ruta).registrar_resultado(muestra, fecha, "Bioquímica", "Normal")


def tabla_de(reporte, indice=0):
    return reporte.tablas[indice].filas


# Reporte 1: atenciones y derivaciones


def test_atenciones_cuenta_por_tipo_y_ordenes_por_clinica(ruta):
    primera = consulta(ruta, tipo="Consulta")
    consulta(ruta, tipo="Consulta", fecha="2026-10-06 10:00")
    consulta(ruta, tipo="Urgencia", fecha="2026-10-07 10:00")
    consulta(ruta, LUNA, RIOS, tipo="Control")
    GestorAtencion(ruta).emitir_orden(primera, 1, "2026-10-05 10:20", [(HEMOGRAMA, "2026-10-05 10:15")], "Laura")
    GestorAtencion(ruta).emitir_orden(primera, 1, "2026-10-05 10:30", [(HEMOGRAMA, "2026-10-05 10:25")], "Laura")
    assert tabla_de(GestorReportes(ruta).atenciones()) == [
        [CENTRO, 2, 0, 1, 3, 2],
        [NORTE, 0, 1, 0, 1, 0],
        [SUR, 0, 0, 0, 0, 0],
    ]


def test_atenciones_filtra_por_periodo_incluyendo_los_extremos(ruta):
    consulta(ruta, fecha="2026-10-01 00:00")
    consulta(ruta, fecha="2026-10-31 23:59")
    consulta(ruta, fecha="2026-09-30 23:59")
    consulta(ruta, fecha="2026-11-01 00:00")
    reporte = GestorReportes(ruta).atenciones("2026-10-01", "2026-10-31")
    assert tabla_de(reporte)[0][4] == 2


def test_atenciones_sin_datos_muestra_las_clinicas_en_cero_y_sin_grafico(ruta):
    reporte = GestorReportes(ruta).atenciones()
    assert tabla_de(reporte) == [[CENTRO, 0, 0, 0, 0, 0], [NORTE, 0, 0, 0, 0, 0], [SUR, 0, 0, 0, 0, 0]]
    assert reporte.graficos == ()


def test_las_ordenes_no_multiplican_las_consultas_al_cruzar_tablas(ruta):
    consulta_id = consulta(ruta)
    for minuto in ("20", "30", "40"):
        GestorAtencion(ruta).emitir_orden(consulta_id, 1, f"2026-10-05 10:{minuto}",
                                          [(HEMOGRAMA, "2026-10-05 10:15")], "Laura")
    assert tabla_de(GestorReportes(ruta).atenciones())[0] == [CENTRO, 1, 0, 0, 1, 3]


# Reporte 2: muestras rechazadas


def test_rechazos_agrupa_e_incluye_remito_y_precinto(ruta):
    muestras, remito = derivar(ruta, consulta(ruta), (HEMOGRAMA, BIOQUIMICO), precinto="Roto")
    reporte = GestorReportes(ruta).rechazos()
    assert tabla_de(reporte, 0) == [[CENTRO, NOMBRE_1, 2]]
    detalle = tabla_de(reporte, 1)
    assert len(detalle) == 2
    assert detalle[0][:5] == [CENTRO, NOMBRE_1, "R-000001", "P-000001", "M-000001"]
    assert detalle[0][5:] == ["Hemograma completo", "2026-10-05 15:00"]


def test_rechazos_atribuye_al_ultimo_transportista(ruta):
    derivar(ruta, consulta(ruta), transportistas=(TRANSPORTE_1, TRANSPORTE_2), precinto="Roto")
    assert tabla_de(GestorReportes(ruta).rechazos(), 0) == [[CENTRO, NOMBRE_2, 1]]


def test_rechazos_no_incluye_muestras_recibidas(ruta):
    derivar(ruta, consulta(ruta))
    reporte = GestorReportes(ruta).rechazos()
    assert tabla_de(reporte, 0) == []
    assert reporte.graficos == ()


def test_rechazos_filtra_por_fecha_de_recepcion(ruta):
    derivar(ruta, consulta(ruta), precinto="Roto")
    assert tabla_de(GestorReportes(ruta).rechazos("2026-10-06", "2026-10-31"), 0) == []
    assert len(tabla_de(GestorReportes(ruta).rechazos("2026-10-05", "2026-10-05"), 0)) == 1


# Reporte 3: tratamientos y vacunas


def test_tratamientos_solo_lista_consultas_con_tratamiento_del_periodo(ruta):
    consulta(ruta, tratamiento="Antibiótico", fecha="2026-10-05 10:00")
    consulta(ruta, tratamiento=None, fecha="2026-10-06 10:00")
    consulta(ruta, tratamiento="   ", fecha="2026-10-07 10:00")
    consulta(ruta, tratamiento="Fuera de período", fecha="2026-12-01 10:00")
    filas = tabla_de(GestorReportes(ruta).tratamientos_y_vacunas("2026-10-01", "2026-10-31"))
    assert [f[5] for f in filas] == ["Antibiótico"]
    assert filas[0][2:4] == ["Toby", "Gómez, Laura"]


def test_vacunas_lista_faltantes_y_vencidas_con_su_responsable(ruta):
    GestorAtencion(ruta).registrar_consulta(TOBY, GOMEZ, "2025-01-10 10:00", "Control", 1000, vacunas=[(1, "L")])
    filas = tabla_de(GestorReportes(ruta).tratamientos_y_vacunas(None, "2026-10-31"), 1)
    toby = next(f for f in filas if f[0] == "Toby")
    assert toby[1:] == ["Perro", "Martínez, Ana", "Séxtuple", "Antirrábica"]


def test_mascota_con_esquema_completo_no_figura_en_vacunas(ruta):
    GestorAtencion(ruta).registrar_consulta(TOBY, GOMEZ, "2026-10-01 10:00", "Control", 1000,
                                            vacunas=[(1, "L"), (2, "L")])
    filas = tabla_de(GestorReportes(ruta).tratamientos_y_vacunas(None, "2026-10-31"), 1)
    assert "Toby" not in [f[0] for f in filas]


def test_vacunas_se_evaluan_al_final_del_periodo(ruta):
    GestorAtencion(ruta).registrar_consulta(TOBY, GOMEZ, "2025-10-01 10:00", "Control", 1000, vacunas=[(1, "L")])
    reportes = GestorReportes(ruta)
    vigente = next(f for f in tabla_de(reportes.tratamientos_y_vacunas(None, "2026-09-30"), 1) if f[0] == "Toby")
    vencida = next(f for f in tabla_de(reportes.tratamientos_y_vacunas(None, "2026-10-31"), 1) if f[0] == "Toby")
    assert vigente[4] == "-"
    assert vencida[4] == "Antirrábica"


# Reporte 4: facturación


def facturar_escenario(ruta):
    con_analisis = consulta(ruta)
    muestras, _ = derivar(ruta, con_analisis, (HEMOGRAMA, BIOQUIMICO))
    analizar(ruta, muestras[0], "2026-10-06 09:00")
    analizar(ruta, muestras[1], "2026-10-06 09:00")
    GestorLaboratorio(ruta).emitir_comprobante(con_analisis, "2026-10-07 10:00")
    GestorLaboratorio(ruta).emitir_comprobante(consulta(ruta, LUNA, RIOS, precio=30000), "2026-10-08 10:00")


def test_facturacion_separa_consultas_y_laboratorio_por_tipo_de_analisis(ruta):
    facturar_escenario(ruta)
    reporte = GestorReportes(ruta).facturacion()
    assert tabla_de(reporte, 0) == [
        [CENTRO, "$ 20000.00", "$ 43000.00", "$ 63000.00"],
        [NORTE, "$ 30000.00", "$ 0.00", "$ 30000.00"],
    ]
    assert tabla_de(reporte, 1) == [
        [CENTRO, "Consultas", 1, "$ 20000.00"],
        [CENTRO, "Hemograma completo", 1, "$ 18000.00"],
        [CENTRO, "Perfil bioquímico", 1, "$ 25000.00"],
        [NORTE, "Consultas", 1, "$ 30000.00"],
    ]


def test_facturacion_coincide_con_los_comprobantes(ruta):
    facturar_escenario(ruta)
    cx = conectar(ruta)
    total_comprobantes = cx.execute("SELECT SUM(total) FROM comprobantes").fetchone()[0]
    cx.close()
    reporte = GestorReportes(ruta).facturacion()
    assert sum(reporte.graficos[0].valores) == total_comprobantes


def test_facturacion_filtra_por_fecha_de_comprobante(ruta):
    facturar_escenario(ruta)
    assert [f[0] for f in tabla_de(GestorReportes(ruta).facturacion("2026-10-08", "2026-10-08"), 0)] == [NORTE]


# Reporte 5: tiempos


def test_tiempos_de_transito_y_procesamiento(ruta):
    muestras, _ = derivar(ruta, consulta(ruta), despacho="12:00", recepcion="15:00")
    analizar(ruta, muestras[0], "2026-10-06 15:00")
    reporte = GestorReportes(ruta).tiempos()
    assert tabla_de(reporte, 0) == [[CENTRO, 1, "3.0"], ["General", 1, "3.0"]]
    assert tabla_de(reporte, 1) == [["Hemograma completo", 1, "24.0"], ["General", 1, "24.0"]]


def test_promedio_general_pondera_por_cantidad(ruta):
    # Dos remitos del Centro de 2 y 4 horas y uno del Norte de 9: el general es 5, no (3 + 9) / 2 = 6.
    derivar(ruta, consulta(ruta), dia="2026-10-05", despacho="12:00", recepcion="14:00")
    derivar(ruta, consulta(ruta), dia="2026-10-06", despacho="12:00", recepcion="16:00")
    derivar(ruta, consulta(ruta, LUNA, RIOS), dia="2026-10-07", despacho="12:00", recepcion="21:00")
    assert tabla_de(GestorReportes(ruta).tiempos(), 0) == [
        [CENTRO, 2, "3.0"], [NORTE, 1, "9.0"], ["General", 3, "5.0"],
    ]


def test_transito_incluye_remitos_rechazados_y_procesamiento_no(ruta):
    derivar(ruta, consulta(ruta), precinto="Roto")
    reporte = GestorReportes(ruta).tiempos()
    assert tabla_de(reporte, 0)[0] == [CENTRO, 1, "3.0"]
    assert tabla_de(reporte, 1) == []


def test_tiempos_no_cuenta_remitos_sin_recibir(ruta):
    consulta_id = consulta(ruta)
    codigos = GestorAtencion(ruta).emitir_orden(consulta_id, 1, "2026-10-05 10:20",
                                                [(HEMOGRAMA, "2026-10-05 10:15")], "Laura")["codigos"]
    envios = GestorEnvios(ruta)
    muestras = [m["id"] for m in envios.listar_muestras_para_empaquetar() if m["codigo"] in codigos]
    remito = envios.empaquetar(muestras, 1, "2026-10-05 11:00", "Laura")["remito_id"]
    envios.registrar_evento(remito, TRANSPORTE_1, "Despacho", "2026-10-05 12:00", "Clínica", 5, "Chofer")
    assert tabla_de(GestorReportes(ruta).tiempos(), 0) == []


# Período


@pytest.mark.parametrize("desde, hasta, mensaje", [
    ("05/10/2026", None, "AAAA-MM-DD"),
    (None, "2026-13-01", "AAAA-MM-DD"),
    ("2026-10-31", "2026-10-01", "posterior"),
])
@pytest.mark.parametrize("tipo", list(NOMBRES_REPORTES))
def test_periodo_invalido_da_un_mensaje_claro(ruta, tipo, desde, hasta, mensaje):
    with pytest.raises(ErrorNegocio, match=mensaje):
        GestorReportes(ruta).generar(tipo, desde, hasta)


def test_reporte_desconocido_es_rechazado(ruta):
    with pytest.raises(ErrorNegocio, match="desconocido"):
        GestorReportes(ruta).generar("inventado")


# Exportación (patrón Factory Method)

FIRMAS = {"PDF": b"%PDF", "Excel": b"PK", "Markdown": b"# "}  # cómo empieza cada tipo de archivo


@pytest.mark.parametrize("formato", FORMATOS)
@pytest.mark.parametrize("tipo", list(NOMBRES_REPORTES))
def test_cada_formato_se_genera_con_y_sin_datos(ruta, tmp_path, tipo, formato):
    gestor = GestorReportes(ruta)
    vacio = gestor.exportar(tipo, gestor.generar(tipo), formato, tmp_path)
    CargaDemo(ruta).cargar()
    con_datos = gestor.exportar(tipo, gestor.generar(tipo), formato, tmp_path)
    assert vacio != con_datos
    for archivo in (vacio, con_datos):
        assert archivo.read_bytes().startswith(FIRMAS[formato])
    assert con_datos.read_bytes() != vacio.read_bytes()


@pytest.mark.parametrize("formato, extension, clase", [
    ("PDF", "pdf", DocumentoPDF),
    ("Excel", "xlsx", DocumentoExcel),
    ("Markdown", "md", DocumentoMarkdown),
])
def test_cada_exportador_crea_su_documento(tmp_path, formato, extension, clase):
    exportador = EXPORTADORES[formato]()
    assert isinstance(exportador, Exportador)
    assert exportador.extension == extension
    assert isinstance(exportador.crear_documento(tmp_path / f"x.{extension}"), clase)


def test_excel_tiene_las_tablas_y_los_graficos(ruta, tmp_path):
    CargaDemo(ruta).cargar()
    gestor = GestorReportes(ruta)
    reporte = gestor.generar(FACTURACION)
    libro = load_workbook(gestor.exportar(FACTURACION, reporte, "Excel", tmp_path))
    valores = [celda for fila in libro["Datos"].iter_rows(values_only=True) for celda in fila if celda]
    assert reporte.titulo in valores
    for tabla in reporte.tablas:
        assert tabla.subtitulo in valores
        assert all(columna in valores for columna in tabla.columnas)
    assert len(libro["Gráficos"]._images) == len(reporte.graficos)


def test_markdown_tiene_las_tablas_y_enlaza_los_graficos(ruta, tmp_path):
    CargaDemo(ruta).cargar()
    gestor = GestorReportes(ruta)
    reporte = gestor.generar(FACTURACION)
    archivo = gestor.exportar(FACTURACION, reporte, "Markdown", tmp_path)
    texto = archivo.read_text(encoding="utf-8")
    assert texto.startswith(f"# {reporte.titulo}")
    for tabla in reporte.tablas:
        assert f"## {tabla.subtitulo}" in texto
        assert "| " + " | ".join(tabla.columnas) + " |" in texto
    imagenes = sorted(tmp_path.glob(f"{archivo.stem}_grafico_*.png"))
    assert len(imagenes) == len(reporte.graficos)
    for imagen in imagenes:
        assert f"]({imagen.name})" in texto
        assert imagen.read_bytes().startswith(b"\x89PNG")


@pytest.mark.parametrize("formato", FORMATOS)
def test_exportar_tolera_textos_con_caracteres_especiales(ruta, tmp_path, formato):
    reporte = Reporte("Prueba <b> & cía", "todo")
    reporte.agregar_tabla("Sub & título", ["A<1", "B|C"], [["R&D <x>", None]])
    archivo = GestorReportes(ruta).exportar("prueba", reporte, formato, tmp_path)
    assert archivo.read_bytes().startswith(FIRMAS[formato])


def test_markdown_escapa_la_barra_para_no_romper_la_tabla(ruta, tmp_path):
    reporte = Reporte("Prueba", "todo")
    reporte.agregar_tabla("Tabla", ["A", "B"], [["x|y", None]])
    texto = GestorReportes(ruta).exportar("prueba", reporte, "Markdown", tmp_path).read_text(encoding="utf-8")
    assert "| x\\|y |  |" in texto


def test_formato_desconocido_es_rechazado(ruta, tmp_path):
    with pytest.raises(ErrorNegocio, match="Formato desconocido"):
        GestorReportes(ruta).exportar(ATENCIONES, GestorReportes(ruta).atenciones(), "Word", tmp_path)


@pytest.mark.parametrize("formato", FORMATOS)
def test_error_al_guardar_da_un_mensaje_claro(ruta, tmp_path, formato):
    ocupado = tmp_path / "archivo"
    ocupado.write_text("no es una carpeta")
    with pytest.raises(ErrorNegocio, match="No se pudo guardar"):
        GestorReportes(ruta).exportar(ATENCIONES, GestorReportes(ruta).atenciones(), formato, ocupado)


# Datos de demostración


def test_demo_produce_datos_en_todos_los_reportes(ruta):
    assert CargaDemo(ruta).cargar() is True
    gestor = GestorReportes(ruta)
    for tipo in NOMBRES_REPORTES:
        reporte = gestor.generar(tipo)
        assert any(tabla.filas for tabla in reporte.tablas)
        assert reporte.graficos


def test_demo_no_se_carga_dos_veces(ruta):
    assert CargaDemo(ruta).cargar() is True
    assert CargaDemo(ruta).cargar() is False


def test_demo_deja_muestras_listas_para_el_laboratorio(ruta):
    CargaDemo(ruta).cargar()
    assert len(GestorLaboratorio(ruta).listar_muestras_recibidas()) == 2


def valores_distintos(ruta, sql):
    conexion = conectar(ruta)
    try:
        return {fila[0] for fila in conexion.execute(sql)}
    finally:
        conexion.close()


def test_demo_cubre_todas_las_opciones(ruta):
    CargaDemo(ruta).cargar()
    assert len(GestorAtencion(ruta).listar_consultas()) == 25
    assert valores_distintos(ruta, "SELECT tipo FROM consultas") == {"Consulta", "Control", "Urgencia"}
    assert valores_distintos(ruta, "SELECT clinica_id FROM consultas") == {1, 2, 3}
    assert valores_distintos(ruta, "SELECT estado FROM turnos") == {"Reservado", "Atendido", "Cancelado"}
    assert valores_distintos(ruta, "SELECT estado_actual FROM muestras") == {
        "Extraída", "Empaquetada", "En tránsito", "Recibida", "Analizada", "Rechazada"}
    assert valores_distintos(ruta, "SELECT estado_actual FROM remitos_biologicos") == {
        "Emitido", "Despachado", "En tránsito", "Recibido", "Rechazado"}
    assert valores_distintos(ruta, "SELECT estado FROM conservadoras") == {"Disponible", "En uso", "Fuera de servicio"}
    assert valores_distintos(ruta, "SELECT tipo_analisis_id FROM muestras") == {1, 2, 3, 4, 5, 6}
    assert valores_distintos(ruta, "SELECT prioridad FROM ordenes_derivacion") == {"Normal", "Urgente"}
    assert valores_distintos(ruta, "SELECT estado_precinto FROM recepciones") == {"Intacto", "Roto"}


# Pantalla


def abrir_reportes(ruta):
    app = Aplicacion(ruta)
    app.abrir(len(app.pantallas) - 1)
    return app.pantallas[-1]


@pytest.mark.parametrize("formato, extension", [("PDF", "pdf"), ("Excel", "xlsx"), ("Markdown", "md")])
def test_pantalla_muestra_el_reporte_y_lo_exporta(ruta, tmp_path, monkeypatch, formato, extension):
    CargaDemo(ruta).cargar()
    pantalla = abrir_reportes(ruta)
    assert pantalla.formato.value == "PDF"
    pantalla.tipo.value = FACTURACION
    pantalla.ver(None)
    assert len(pantalla.resultado.controls) == 4
    original = pantalla.gestor.exportar
    monkeypatch.setattr(pantalla.gestor, "exportar",
                        lambda tipo, reporte, formato: original(tipo, reporte, formato, tmp_path))
    pantalla.formato.value = formato
    pantalla.exportar(None)
    assert f"{formato} guardado" in pantalla.mensaje.value
    assert list(tmp_path.glob(f"facturacion_*.{extension}"))


def test_pantalla_avisa_si_no_hay_datos_o_falta_elegir(ruta):
    pantalla = abrir_reportes(ruta)
    pantalla.ver(None)
    assert pantalla.mensaje.value == "Debe seleccionar: Reporte"
    pantalla.tipo.value = RECHAZOS
    pantalla.ver(None)
    textos = [c.value for c in pantalla.resultado.controls if hasattr(c, "value")]
    assert "Sin datos para el período elegido." in textos


def test_pantalla_muestra_el_error_de_periodo(ruta):
    pantalla = abrir_reportes(ruta)
    pantalla.tipo.value = TIEMPOS
    pantalla.desde.value = "ayer"
    pantalla.ver(None)
    assert "AAAA-MM-DD" in pantalla.mensaje.value
    pantalla.tipo.value = TRATAMIENTOS
    pantalla.desde.value = ""
    pantalla.ver(None)
    assert "Período" in pantalla.mensaje.value
