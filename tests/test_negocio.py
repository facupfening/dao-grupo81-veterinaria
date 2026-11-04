import pytest

from datos.base_datos import conectar, inicializar
from negocio.gestor import ErrorNegocio
from negocio.gestor_atencion import GestorAtencion
from negocio.gestor_clientes import GestorClientes
from negocio.gestor_envios import GestorEnvios
from negocio.gestor_laboratorio import GestorLaboratorio
from negocio.gestor_mascotas import GestorMascotas

RESPONSABLE = "Laura Gómez"
HEMOGRAMA, BIOQUIMICO, HISTOPATOLOGIA = 1, 2, 5
REF_01, AMB_01, REF_03 = 1, 3, 5
TOBY, LUNA = 1, 3
LABORATORIO, TRANSPORTISTA = 1, 1
PRECIO_CONSULTA = 20000


@pytest.fixture
def ruta(tmp_path):
    ruta = tmp_path / "prueba.db"
    inicializar(ruta)
    return ruta


def contar(ruta, tabla):
    cx = conectar(ruta)
    cantidad = cx.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
    cx.close()
    return cantidad


def crear_consulta(ruta, mascota_id=TOBY, veterinario_id=1):
    return GestorAtencion(ruta).registrar_consulta(
        mascota_id, veterinario_id, "2026-11-03 10:00", "Consulta", PRECIO_CONSULTA
    )["consulta_id"]


def crear_muestras(ruta, tipos=(HEMOGRAMA,), mascota_id=TOBY, veterinario_id=1):
    """Devuelve la consulta y los ids de las muestras creadas."""
    consulta_id = crear_consulta(ruta, mascota_id, veterinario_id)
    GestorAtencion(ruta).emitir_orden(
        consulta_id, LABORATORIO, "2026-11-03 10:20",
        [(tipo, "2026-11-03 10:15") for tipo in tipos], RESPONSABLE,
    )
    cx = conectar(ruta)
    filas = cx.execute(
        """SELECT m.id FROM muestras m JOIN ordenes_derivacion o ON o.id = m.orden_id
           WHERE o.consulta_id = ? ORDER BY m.id""",
        (consulta_id,),
    ).fetchall()
    cx.close()
    return consulta_id, [fila["id"] for fila in filas]


def crear_remito(ruta, tipos=(HEMOGRAMA, BIOQUIMICO)):
    consulta_id, muestras = crear_muestras(ruta, tipos)
    remito = GestorEnvios(ruta).empaquetar(muestras, REF_01, "2026-11-03 11:00", RESPONSABLE)
    return consulta_id, muestras, remito["remito_id"]


def poner_en_transito(ruta, remito_id):
    gestor = GestorEnvios(ruta)
    gestor.registrar_evento(remito_id, TRANSPORTISTA, "Despacho", "2026-11-03 12:00", "Clínica Centro", 5, "Chofer")
    gestor.registrar_evento(remito_id, TRANSPORTISTA, "Arribo", "2026-11-03 14:00", "Laboratorio", 6, "Chofer")


def recibir(ruta, remito_id, precinto="Intacto"):
    return GestorEnvios(ruta).registrar_recepcion(remito_id, precinto, "2026-11-03 15:00", "Bioquímica", 6)


def remito_recibido(ruta, precinto="Intacto"):
    consulta_id, muestras, remito_id = crear_remito(ruta)
    poner_en_transito(ruta, remito_id)
    recibir(ruta, remito_id, precinto)
    return consulta_id, muestras, remito_id


def estados_de_muestras(ruta, muestras):
    cx = conectar(ruta)
    estados = [cx.execute("SELECT estado_actual FROM muestras WHERE id = ?", (m,)).fetchone()[0] for m in muestras]
    cx.close()
    return estados


def estado_conservadora(ruta, id):
    cx = conectar(ruta)
    estado = cx.execute("SELECT estado FROM conservadoras WHERE id = ?", (id,)).fetchone()[0]
    cx.close()
    return estado


# 1. Clientes


def test_alta_modificacion_y_consulta_de_cliente(ruta):
    gestor = GestorClientes(ruta)
    id = gestor.alta("40111222", "Marta", "Paz", email="marta@example.com")
    assert gestor.obtener_por_dni("40111222").id == id
    gestor.modificar(id, "40111222", "Marta", "Paz Díaz")
    assert gestor.obtener(id).apellido == "Paz Díaz"
    assert [c.id for c in gestor.buscar_por_apellido("Díaz")] == [id]


@pytest.mark.parametrize("dni", ["", "123", "abc45678", "123456789", None])
def test_cliente_con_dni_invalido_es_rechazado(ruta, dni):
    with pytest.raises(ErrorNegocio):
        GestorClientes(ruta).alta(dni, "Marta", "Paz")


def test_cliente_sin_nombre_es_rechazado(ruta):
    with pytest.raises(ErrorNegocio, match="Nombre"):
        GestorClientes(ruta).alta("40111222", "  ", "Paz")


def test_dni_repetido_da_un_mensaje_claro(ruta):
    with pytest.raises(ErrorNegocio, match="Ya existe un cliente con DNI 30000001"):
        GestorClientes(ruta).alta("30000001", "Otra", "Persona")


def test_no_se_puede_cambiar_el_dni_por_el_de_otro_cliente(ruta):
    with pytest.raises(ErrorNegocio, match="Ya existe"):
        GestorClientes(ruta).modificar(2, "30000001", "Carlos", "López")


def test_modificar_conservando_su_propio_dni_esta_permitido(ruta):
    GestorClientes(ruta).modificar(1, "30000001", "Ana María", "Martínez")
    assert GestorClientes(ruta).obtener(1).nombre == "Ana María"


def test_cliente_con_mascotas_no_se_da_de_baja(ruta):
    with pytest.raises(ErrorNegocio, match="mascotas asociadas"):
        GestorClientes(ruta).baja(1)


def test_cliente_sin_mascotas_se_da_de_baja(ruta):
    gestor = GestorClientes(ruta)
    id = gestor.alta("40111222", "Marta", "Paz")
    gestor.baja(id)
    assert gestor.obtener(id) is None


# 2. Mascotas e historias clínicas


def test_alta_de_mascota_abre_su_historia(ruta):
    gestor = GestorMascotas(ruta)
    id = gestor.alta(2, 1, "Rocco", "2026-11-03 09:00", antecedentes="Displasia")
    historia = gestor.obtener_historia(id)
    assert historia["historia"]["antecedentes"] == "Displasia"
    assert historia["consultas"] == []


@pytest.mark.parametrize("cliente_id", [None, 0])
def test_mascota_sin_responsable_es_rechazada(ruta, cliente_id):
    with pytest.raises(ErrorNegocio, match="responsable"):
        GestorMascotas(ruta).alta(cliente_id, 1, "Rocco", "2026-11-03 09:00")


def test_mascota_con_responsable_inexistente_es_rechazada(ruta):
    with pytest.raises(ErrorNegocio, match="responsable no existe"):
        GestorMascotas(ruta).alta(999, 1, "Rocco", "2026-11-03 09:00")


def test_error_en_el_alta_no_deja_mascota_sin_historia(ruta):
    antes = contar(ruta, "mascotas")
    with pytest.raises(ErrorNegocio):
        GestorMascotas(ruta).alta(2, 1, "Rocco", "fecha mala")
    assert contar(ruta, "mascotas") == antes


@pytest.mark.parametrize("fecha", ["2026-13-01", "03/11/2026", "2026-1-5"])
def test_fecha_de_nacimiento_invalida_es_rechazada(ruta, fecha):
    with pytest.raises(ErrorNegocio, match="AAAA-MM-DD"):
        GestorMascotas(ruta).alta(2, 1, "Rocco", "2026-11-03 09:00", fecha_nacimiento=fecha)


def test_baja_de_mascota_sin_atenciones_borra_tambien_su_historia(ruta):
    gestor = GestorMascotas(ruta)
    historias = contar(ruta, "historias_clinicas")
    id = gestor.alta(2, 1, "Rocco", "2026-11-03 09:00")
    gestor.baja(id)
    assert gestor.obtener(id) is None
    assert contar(ruta, "historias_clinicas") == historias


def test_mascota_con_consultas_no_se_da_de_baja(ruta):
    crear_consulta(ruta)
    with pytest.raises(ErrorNegocio, match="turnos o consultas"):
        GestorMascotas(ruta).baja(TOBY)


def test_mascota_con_turno_no_se_da_de_baja(ruta):
    GestorAtencion(ruta).reservar_turno(LUNA, 1, "2026-11-03 10:00", "2026-11-03 10:30")
    with pytest.raises(ErrorNegocio, match="turnos o consultas"):
        GestorMascotas(ruta).baja(LUNA)


# 3. Turnos, consultas, vacunas y órdenes


def test_turno_superpuesto_da_un_mensaje_claro(ruta):
    gestor = GestorAtencion(ruta)
    gestor.reservar_turno(TOBY, 1, "2026-11-03 10:00", "2026-11-03 10:30")
    with pytest.raises(ErrorNegocio, match="ya tiene un turno"):
        gestor.reservar_turno(LUNA, 1, "2026-11-03 10:15", "2026-11-03 10:45")


def test_turno_que_termina_antes_de_empezar_es_rechazado(ruta):
    with pytest.raises(ErrorNegocio, match="terminar después"):
        GestorAtencion(ruta).reservar_turno(TOBY, 1, "2026-11-03 10:30", "2026-11-03 10:00")


def test_consulta_con_turno_lo_marca_atendido(ruta):
    gestor = GestorAtencion(ruta)
    turno_id = gestor.reservar_turno(TOBY, 1, "2026-11-03 10:00", "2026-11-03 10:30")
    gestor.registrar_consulta(TOBY, 1, "2026-11-03 10:05", "Control", 1000, turno_id=turno_id)
    assert gestor.listar_turnos(1)[0]["estado"] == "Atendido"


def test_turno_atendido_no_se_atiende_ni_se_cancela_de_nuevo(ruta):
    gestor = GestorAtencion(ruta)
    turno_id = gestor.reservar_turno(TOBY, 1, "2026-11-03 10:00", "2026-11-03 10:30")
    gestor.registrar_consulta(TOBY, 1, "2026-11-03 10:05", "Control", 1000, turno_id=turno_id)
    with pytest.raises(ErrorNegocio, match="estado Atendido"):
        gestor.registrar_consulta(TOBY, 1, "2026-11-03 10:20", "Control", 1000, turno_id=turno_id)
    with pytest.raises(ErrorNegocio, match="estado Atendido"):
        gestor.cancelar_turno(turno_id)


def test_turno_de_otra_mascota_es_rechazado_sin_dejar_consulta(ruta):
    gestor = GestorAtencion(ruta)
    turno_id = gestor.reservar_turno(LUNA, 1, "2026-11-03 10:00", "2026-11-03 10:30")
    with pytest.raises(ErrorNegocio, match="otra mascota"):
        gestor.registrar_consulta(TOBY, 1, "2026-11-03 10:05", "Control", 1000, turno_id=turno_id)
    assert contar(ruta, "consultas") == 0


def test_urgencia_sin_turno_toma_la_clinica_del_veterinario(ruta):
    consulta_id = GestorAtencion(ruta).registrar_consulta(TOBY, 3, "2026-11-03 02:00", "Urgencia", 5000)["consulta_id"]
    cx = conectar(ruta)
    fila = cx.execute("SELECT clinica_id, turno_id FROM consultas WHERE id = ?", (consulta_id,)).fetchone()
    cx.close()
    assert fila["clinica_id"] == 2
    assert fila["turno_id"] is None


def test_consulta_informa_vacunas_pendientes(ruta):
    resultado = GestorAtencion(ruta).registrar_consulta(TOBY, 1, "2026-11-03 10:00", "Control", 1000)
    assert sorted(resultado["vacunas_pendientes"]) == ["Antirrábica", "Séxtuple"]
    assert resultado["vacunas_vencidas"] == []


def test_vacuna_aplicada_deja_de_estar_pendiente_y_calcula_la_proxima_dosis(ruta):
    gestor = GestorAtencion(ruta)
    resultado = gestor.registrar_consulta(TOBY, 1, "2026-11-03 10:00", "Control", 1000, vacunas=[(1, "L-1")])
    assert resultado["vacunas_pendientes"] == ["Séxtuple"]
    aplicacion = GestorMascotas(ruta).obtener_historia(TOBY)["vacunas"][0]
    assert aplicacion["fecha_proxima"] == "2027-11-03 10:00"


def test_vacuna_vencida_se_informa_y_una_nueva_dosis_la_regulariza(ruta):
    gestor = GestorAtencion(ruta)
    gestor.registrar_consulta(TOBY, 1, "2025-01-10 10:00", "Control", 1000, vacunas=[(1, "L-1")])
    assert "Antirrábica" in gestor.esquema_vacunas(TOBY, "2026-11-03 10:00")["vacunas_vencidas"]
    resultado = gestor.registrar_consulta(TOBY, 1, "2026-11-03 10:00", "Control", 1000, vacunas=[(1, "L-2")])
    assert resultado["vacunas_vencidas"] == []


def test_vacuna_de_otra_especie_es_rechazada_sin_dejar_consulta(ruta):
    with pytest.raises(ErrorNegocio, match="no corresponde a la especie"):
        GestorAtencion(ruta).registrar_consulta(TOBY, 1, "2026-11-03 10:00", "Control", 1000, vacunas=[(4, "L-1")])
    assert contar(ruta, "consultas") == 0


def test_orden_crea_muestras_extraidas_con_historial(ruta):
    _, muestras = crear_muestras(ruta, (HEMOGRAMA, BIOQUIMICO))
    assert estados_de_muestras(ruta, muestras) == ["Extraída", "Extraída"]
    assert contar(ruta, "historial_estados_muestra") == 2


def test_orden_sin_muestras_es_rechazada(ruta):
    consulta_id = crear_consulta(ruta)
    with pytest.raises(ErrorNegocio, match="al menos una muestra"):
        GestorAtencion(ruta).emitir_orden(consulta_id, LABORATORIO, "2026-11-03 10:20", [], RESPONSABLE)


def test_orden_con_un_analisis_inexistente_no_deja_nada_a_medias(ruta):
    consulta_id = crear_consulta(ruta)
    with pytest.raises(ErrorNegocio, match="análisis no existe"):
        GestorAtencion(ruta).emitir_orden(
            consulta_id, LABORATORIO, "2026-11-03 10:20",
            [(HEMOGRAMA, "2026-11-03 10:15"), (999, "2026-11-03 10:15")], RESPONSABLE,
        )
    assert contar(ruta, "ordenes_derivacion") == 0
    assert contar(ruta, "muestras") == 0


# 4. Empaquetado


def test_empaquetar_genera_remito_y_precinto_y_ocupa_la_conservadora(ruta):
    _, muestras = crear_muestras(ruta, (HEMOGRAMA, BIOQUIMICO))
    resultado = GestorEnvios(ruta).empaquetar(muestras, REF_01, "2026-11-03 11:00", RESPONSABLE)
    remito = GestorEnvios(ruta).obtener_remito(resultado["remito_id"])
    assert remito.estado == "Emitido"
    assert {m.estado for m in remito.muestras} == {"Empaquetada"}
    assert resultado["precinto"].startswith("P-")
    assert estado_conservadora(ruta, REF_01) == "En uso"


def test_muestras_extraidas_figuran_para_empaquetar_hasta_que_se_empaquetan(ruta):
    _, muestras = crear_muestras(ruta)
    gestor = GestorEnvios(ruta)
    assert [m["id"] for m in gestor.listar_muestras_para_empaquetar()] == muestras
    gestor.empaquetar(muestras, REF_01, "2026-11-03 11:00", RESPONSABLE)
    assert gestor.listar_muestras_para_empaquetar() == []


def test_conservadora_de_temperatura_incompatible_es_rechazada(ruta):
    _, muestras = crear_muestras(ruta)
    with pytest.raises(ErrorNegocio, match="no es compatible"):
        GestorEnvios(ruta).empaquetar(muestras, AMB_01, "2026-11-03 11:00", RESPONSABLE)
    assert estados_de_muestras(ruta, muestras) == ["Extraída"]
    assert contar(ruta, "remitos_biologicos") == 0


def test_analisis_con_rangos_distintos_no_comparten_conservadora(ruta):
    _, muestras = crear_muestras(ruta, (HEMOGRAMA, HISTOPATOLOGIA))
    with pytest.raises(ErrorNegocio, match="no es compatible"):
        GestorEnvios(ruta).empaquetar(muestras, REF_01, "2026-11-03 11:00", RESPONSABLE)


def test_conservadora_fuera_de_servicio_es_rechazada(ruta):
    _, muestras = crear_muestras(ruta)
    with pytest.raises(ErrorNegocio, match="no está disponible"):
        GestorEnvios(ruta).empaquetar(muestras, REF_03, "2026-11-03 11:00", RESPONSABLE)


def test_conservadora_en_uso_es_rechazada(ruta):
    crear_remito(ruta)
    _, muestras = crear_muestras(ruta)
    with pytest.raises(ErrorNegocio, match="no está disponible"):
        GestorEnvios(ruta).empaquetar(muestras, REF_01, "2026-11-03 11:00", RESPONSABLE)


def test_capacidad_de_la_conservadora_se_respeta(ruta):
    # REF-02 admite 6 muestras.
    _, muestras = crear_muestras(ruta, (HEMOGRAMA,) * 7)
    with pytest.raises(ErrorNegocio, match="admite 6"):
        GestorEnvios(ruta).empaquetar(muestras, 2, "2026-11-03 11:00", RESPONSABLE)


def test_muestras_de_distintas_clinicas_no_comparten_remito(ruta):
    _, centro = crear_muestras(ruta, veterinario_id=1)
    _, norte = crear_muestras(ruta, mascota_id=LUNA, veterinario_id=3)
    with pytest.raises(ErrorNegocio, match="misma clínica"):
        GestorEnvios(ruta).empaquetar(centro + norte, REF_01, "2026-11-03 11:00", RESPONSABLE)


def test_muestra_ya_empaquetada_no_entra_en_otro_remito_y_nada_queda_a_medias(ruta):
    _, muestras, _ = crear_remito(ruta)
    remitos = contar(ruta, "remitos_biologicos")
    with pytest.raises(ErrorNegocio, match="estado Empaquetada"):
        GestorEnvios(ruta).empaquetar(muestras, 2, "2026-11-03 11:30", RESPONSABLE)
    assert contar(ruta, "remitos_biologicos") == remitos
    assert estado_conservadora(ruta, 2) == "Disponible"


def test_seleccion_vacia_o_repetida_es_rechazada(ruta):
    _, muestras = crear_muestras(ruta)
    with pytest.raises(ErrorNegocio, match="al menos una"):
        GestorEnvios(ruta).empaquetar([], REF_01, "2026-11-03 11:00", RESPONSABLE)
    with pytest.raises(ErrorNegocio, match="repetidas"):
        GestorEnvios(ruta).empaquetar(muestras * 2, REF_01, "2026-11-03 11:00", RESPONSABLE)


# 5. Cadena de envío


def test_cadena_de_envio_mueve_remito_y_muestras(ruta):
    _, muestras, remito_id = crear_remito(ruta)
    gestor = GestorEnvios(ruta)
    gestor.registrar_evento(remito_id, TRANSPORTISTA, "Despacho", "2026-11-03 12:00", "Clínica", 5, "Chofer")
    assert gestor.obtener_remito(remito_id).estado == "Despachado"
    assert estados_de_muestras(ruta, muestras) == ["Empaquetada", "Empaquetada"]
    gestor.registrar_evento(remito_id, 2, "Traspaso", "2026-11-03 13:00", "Depósito", 6, "Otro chofer")
    assert gestor.obtener_remito(remito_id).estado == "En tránsito"
    assert estados_de_muestras(ruta, muestras) == ["En tránsito", "En tránsito"]
    gestor.registrar_evento(remito_id, 2, "Arribo", "2026-11-03 14:00", "Laboratorio", 6, "Otro chofer")
    remito = gestor.obtener_remito(remito_id)
    assert remito.estado == "En tránsito"
    assert [r.estado for r in remito.historial] == ["Emitido", "Despachado", "En tránsito"]
    assert contar(ruta, "eventos_envio") == 3


def test_traspaso_sin_despacho_no_registra_el_evento(ruta):
    _, _, remito_id = crear_remito(ruta)
    with pytest.raises(ErrorNegocio, match="estado Emitido"):
        GestorEnvios(ruta).registrar_evento(remito_id, TRANSPORTISTA, "Traspaso", "2026-11-03 12:00", "Depósito", 5, "Chofer")
    assert contar(ruta, "eventos_envio") == 0


def test_segundo_despacho_es_rechazado(ruta):
    _, _, remito_id = crear_remito(ruta)
    gestor = GestorEnvios(ruta)
    gestor.registrar_evento(remito_id, TRANSPORTISTA, "Despacho", "2026-11-03 12:00", "Clínica", 5, "Chofer")
    with pytest.raises(ErrorNegocio, match="estado Despachado"):
        gestor.registrar_evento(remito_id, TRANSPORTISTA, "Despacho", "2026-11-03 12:30", "Clínica", 5, "Chofer")


def test_evento_con_tipo_o_fecha_invalidos_es_rechazado(ruta):
    _, _, remito_id = crear_remito(ruta)
    gestor = GestorEnvios(ruta)
    with pytest.raises(ErrorNegocio, match="Tipo de evento"):
        gestor.registrar_evento(remito_id, TRANSPORTISTA, "Paseo", "2026-11-03 12:00", "Clínica", 5, "Chofer")
    with pytest.raises(ErrorNegocio, match="formato"):
        gestor.registrar_evento(remito_id, TRANSPORTISTA, "Despacho", "ayer", "Clínica", 5, "Chofer")


def test_evento_anterior_a_la_emision_es_rechazado(ruta):
    _, _, remito_id = crear_remito(ruta)
    with pytest.raises(ErrorNegocio, match="no puede ser anterior"):
        GestorEnvios(ruta).registrar_evento(remito_id, TRANSPORTISTA, "Despacho", "2026-11-03 09:00", "Clínica", 5, "Chofer")


# 6. Recepción


def test_precinto_intacto_recibe_todo_y_libera_la_conservadora(ruta):
    _, muestras, remito_id = crear_remito(ruta)
    poner_en_transito(ruta, remito_id)
    assert recibir(ruta, remito_id) == "Recibido"
    assert estados_de_muestras(ruta, muestras) == ["Recibida", "Recibida"]
    assert estado_conservadora(ruta, REF_01) == "Disponible"


def test_precinto_roto_rechaza_todo_y_libera_la_conservadora(ruta):
    _, muestras, remito_id = crear_remito(ruta)
    poner_en_transito(ruta, remito_id)
    assert recibir(ruta, remito_id, "Roto") == "Rechazado"
    assert estados_de_muestras(ruta, muestras) == ["Rechazada", "Rechazada"]
    assert estado_conservadora(ruta, REF_01) == "Disponible"


def test_recepcion_de_remito_no_transitado_no_registra_nada(ruta):
    _, _, remito_id = crear_remito(ruta)
    with pytest.raises(ErrorNegocio, match="estado Emitido"):
        recibir(ruta, remito_id)
    assert contar(ruta, "recepciones") == 0
    assert estado_conservadora(ruta, REF_01) == "En uso"


def test_segunda_recepcion_es_rechazada(ruta):
    _, _, remito_id = remito_recibido(ruta)
    with pytest.raises(ErrorNegocio, match="estado Recibido"):
        recibir(ruta, remito_id)
    assert contar(ruta, "recepciones") == 1


# 7. Resultados y comprobantes


def test_resultado_de_muestra_recibida_la_deja_analizada(ruta):
    _, muestras, _ = remito_recibido(ruta)
    GestorLaboratorio(ruta).registrar_resultado(muestras[0], "2026-11-04 09:00", "Bioquímica", "Hto 45%", "Normal")
    assert estados_de_muestras(ruta, muestras) == ["Analizada", "Recibida"]


def test_muestra_rechazada_no_admite_resultado_y_no_deja_rastro(ruta):
    _, muestras, _ = remito_recibido(ruta, "Roto")
    with pytest.raises(ErrorNegocio, match="estado Rechazada"):
        GestorLaboratorio(ruta).registrar_resultado(muestras[0], "2026-11-04 09:00", "Bioquímica", "Hto 45%")
    assert contar(ruta, "resultados") == 0


def test_muestra_sin_recibir_no_admite_resultado(ruta):
    _, muestras = crear_muestras(ruta)
    with pytest.raises(ErrorNegocio, match="estado Extraída"):
        GestorLaboratorio(ruta).registrar_resultado(muestras[0], "2026-11-04 09:00", "Bioquímica", "Hto 45%")


def test_muestra_no_admite_dos_resultados(ruta):
    _, muestras, _ = remito_recibido(ruta)
    gestor = GestorLaboratorio(ruta)
    gestor.registrar_resultado(muestras[0], "2026-11-04 09:00", "Bioquímica", "Hto 45%")
    with pytest.raises(ErrorNegocio, match="estado Analizada"):
        gestor.registrar_resultado(muestras[0], "2026-11-04 10:00", "Bioquímica", "Hto 46%")


def test_comprobante_tiene_una_linea_por_consulta_y_por_analisis_realizado(ruta):
    consulta_id, muestras, _ = remito_recibido(ruta)
    gestor = GestorLaboratorio(ruta)
    gestor.registrar_resultado(muestras[0], "2026-11-04 09:00", "Bioquímica", "Hto 45%")
    gestor.registrar_resultado(muestras[1], "2026-11-04 09:00", "Bioquímica", "Glucosa 90")
    resultado = gestor.emitir_comprobante(consulta_id, "2026-11-04 10:00")
    # Hemograma 18000 + Perfil bioquímico 25000.
    assert resultado["total"] == PRECIO_CONSULTA + 18000 + 25000
    comprobante = gestor.obtener_comprobante(resultado["comprobante_id"])
    assert comprobante["comprobante"]["cliente_id"] == 1
    assert comprobante["comprobante"]["clinica_id"] == 1
    assert len(comprobante["detalles"]) == 3


def test_muestras_rechazadas_no_se_facturan(ruta):
    consulta_id, _, _ = remito_recibido(ruta, "Roto")
    resultado = GestorLaboratorio(ruta).emitir_comprobante(consulta_id, "2026-11-04 10:00")
    assert resultado["total"] == PRECIO_CONSULTA
    assert len(GestorLaboratorio(ruta).obtener_comprobante(resultado["comprobante_id"])["detalles"]) == 1


def test_analisis_posterior_se_factura_en_otro_comprobante_sin_repetir_lineas(ruta):
    consulta_id, muestras, _ = remito_recibido(ruta)
    gestor = GestorLaboratorio(ruta)
    gestor.registrar_resultado(muestras[0], "2026-11-04 09:00", "Bioquímica", "Hto 45%")
    primero = gestor.emitir_comprobante(consulta_id, "2026-11-04 10:00")
    assert primero["total"] == PRECIO_CONSULTA + 18000
    with pytest.raises(ErrorNegocio, match="pendientes de facturar"):
        gestor.emitir_comprobante(consulta_id, "2026-11-04 10:30")
    gestor.registrar_resultado(muestras[1], "2026-11-04 11:00", "Bioquímica", "Glucosa 90")
    segundo = gestor.emitir_comprobante(consulta_id, "2026-11-04 12:00")
    assert segundo["total"] == 25000
    assert segundo["numero"] != primero["numero"]


# Trazabilidad completa


def test_historia_clinica_reune_todo_el_recorrido(ruta):
    consulta_id, muestras, _ = remito_recibido(ruta)
    GestorLaboratorio(ruta).registrar_resultado(muestras[0], "2026-11-04 09:00", "Bioquímica", "Hto 45%")
    historia = GestorMascotas(ruta).obtener_historia(TOBY)
    assert [c["id"] for c in historia["consultas"]] == [consulta_id]
    primera = historia["ordenes"][0]["muestras"][0]
    assert primera["muestra"].estado == "Analizada"
    assert primera["resultado"]["valores"] == "Hto 45%"
    assert [r.estado for r in primera["muestra"].historial] == [
        "Extraída", "Empaquetada", "En tránsito", "Recibida", "Analizada",
    ]


def test_el_historial_guardado_coincide_con_el_estado_actual(ruta):
    remito_recibido(ruta, "Roto")
    cx = conectar(ruta)
    desalineadas = cx.execute(
        """SELECT COUNT(*) FROM muestras m
           WHERE m.estado_actual <> (SELECT h.estado FROM historial_estados_muestra h
                                     WHERE h.muestra_id = m.id ORDER BY h.id DESC LIMIT 1)"""
    ).fetchone()[0]
    assert desalineadas == 0
    assert cx.execute("PRAGMA foreign_key_check").fetchall() == []
    cx.close()
