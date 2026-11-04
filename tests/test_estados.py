import pytest

from datos.base_datos import cargar_datos_ejemplo, conectar, crear_tablas
from estados.estado_muestra import ESTADOS_MUESTRA, EstadoMuestra
from estados.estado_remito import ESTADOS_REMITO, EstadoRemito
from estados.transicion_invalida import TransicionInvalida
from modelos.muestra import Muestra
from modelos.registro_estado import RegistroEstado
from modelos.remito import Remito

FECHA = "2026-11-03 10:00"
RESPONSABLE = "Laura Gómez"

# Para cada estado de la muestra, qué operaciones admite.
OPERACIONES_MUESTRA = ["empaquetar", "iniciar_transito", "recibir", "rechazar", "analizar"]
PERMITIDAS_MUESTRA = {
    "Extraída": {"empaquetar": "Empaquetada"},
    "Empaquetada": {"iniciar_transito": "En tránsito"},
    "En tránsito": {"recibir": "Recibida", "rechazar": "Rechazada"},
    "Recibida": {"analizar": "Analizada"},
    "Analizada": {},
    "Rechazada": {},
}


def crear_muestra(codigo="M-1", estado="Extraída"):
    historial = None if estado == "Extraída" else [RegistroEstado(estado, FECHA, RESPONSABLE)]
    return Muestra(codigo, 1, 1, FECHA, RESPONSABLE, estado=estado, historial=historial)


def crear_remito():
    return Remito("R-1", 1, 1, 1, FECHA, RESPONSABLE)


def remito_con_muestras(cantidad=2):
    remito = crear_remito()
    for i in range(cantidad):
        remito.agregar_muestra(crear_muestra(f"M-{i}"), FECHA, RESPONSABLE)
    return remito


def remito_en_transito(cantidad=2):
    remito = remito_con_muestras(cantidad)
    remito.despachar(FECHA, RESPONSABLE)
    remito.registrar_tramo(FECHA, RESPONSABLE)
    return remito


def estados_de(remito):
    return {muestra.estado for muestra in remito.muestras}


# Muestra: todas las combinaciones de estado y operación


CASOS_MUESTRA = [(estado, operacion) for estado in PERMITIDAS_MUESTRA for operacion in OPERACIONES_MUESTRA]


@pytest.mark.parametrize("estado, operacion", CASOS_MUESTRA)
def test_transiciones_de_muestra(estado, operacion):
    muestra = crear_muestra(estado=estado)
    destino = PERMITIDAS_MUESTRA[estado].get(operacion)
    if destino:
        getattr(muestra, operacion)(FECHA, RESPONSABLE)
        assert muestra.estado == destino
        assert muestra.historial[-1].estado == destino
    else:
        cantidad = len(muestra.historial)
        with pytest.raises(TransicionInvalida):
            getattr(muestra, operacion)(FECHA, RESPONSABLE)
        assert muestra.estado == estado
        assert len(muestra.historial) == cantidad


def test_muestra_nace_extraida_con_su_primer_registro():
    muestra = crear_muestra()
    assert muestra.estado == "Extraída"
    assert [registro.estado for registro in muestra.historial] == ["Extraída"]
    assert muestra.historial[0].responsable == RESPONSABLE


def test_muestra_rechazada_no_admite_resultados():
    muestra = crear_muestra(estado="Rechazada")
    with pytest.raises(TransicionInvalida, match="No se puede analizar una muestra en estado Rechazada"):
        muestra.analizar(FECHA, RESPONSABLE)


# Historial


def test_historial_no_se_puede_alterar_desde_afuera():
    muestra = crear_muestra()
    assert isinstance(muestra.historial, tuple)
    with pytest.raises(AttributeError):
        muestra.historial = []
    with pytest.raises(AttributeError):
        muestra.historial[0].estado = "Analizada"


def test_historial_rechaza_fechas_anteriores_al_ultimo_registro():
    muestra = crear_muestra()
    with pytest.raises(ValueError, match="no puede ser anterior"):
        muestra.empaquetar("2026-11-02 10:00", RESPONSABLE)
    assert muestra.estado == "Extraída"


@pytest.mark.parametrize("fecha, responsable", [("", RESPONSABLE), (FECHA, ""), (None, RESPONSABLE), (FECHA, None)])
def test_cambio_de_estado_exige_fecha_y_responsable(fecha, responsable):
    muestra = crear_muestra()
    with pytest.raises(ValueError):
        muestra.empaquetar(fecha, responsable)
    assert muestra.estado == "Extraída"


def test_muestra_nueva_exige_responsable():
    with pytest.raises(ValueError):
        Muestra("M-1", 1, 1, FECHA)


def test_muestra_recuperada_conserva_estado_e_historial():
    historial = [
        RegistroEstado("Extraída", "2026-11-03 09:00", RESPONSABLE),
        RegistroEstado("Empaquetada", "2026-11-03 10:00", RESPONSABLE),
    ]
    muestra = Muestra("M-1", 1, 1, "2026-11-03 09:00", estado="Empaquetada", historial=historial, id=7)
    assert muestra.estado == "Empaquetada"
    assert len(muestra.historial) == 2
    muestra.iniciar_transito("2026-11-03 11:00", RESPONSABLE)
    assert muestra.estado == "En tránsito"
    assert len(muestra.historial) == 3


# Remito: empaquetado


def test_remito_nace_emitido_con_su_primer_registro():
    remito = crear_remito()
    assert remito.estado == "Emitido"
    assert [registro.estado for registro in remito.historial] == ["Emitido"]


def test_agregar_muestra_la_empaqueta():
    remito = remito_con_muestras(1)
    assert estados_de(remito) == {"Empaquetada"}


def test_no_se_agrega_una_muestra_ya_empaquetada():
    remito = crear_remito()
    muestra = crear_muestra()
    remito.agregar_muestra(muestra, FECHA, RESPONSABLE)
    otro_remito = Remito("R-2", 1, 1, 1, FECHA, RESPONSABLE)
    with pytest.raises(TransicionInvalida):
        otro_remito.agregar_muestra(muestra, FECHA, RESPONSABLE)
    assert otro_remito.muestras == ()


def test_no_se_despacha_un_remito_sin_muestras():
    remito = crear_remito()
    with pytest.raises(TransicionInvalida, match="sin muestras"):
        remito.despachar(FECHA, RESPONSABLE)
    assert remito.estado == "Emitido"


def test_no_se_agregan_muestras_despues_del_despacho():
    remito = remito_con_muestras(1)
    remito.despachar(FECHA, RESPONSABLE)
    muestra = crear_muestra("M-9")
    with pytest.raises(TransicionInvalida):
        remito.agregar_muestra(muestra, FECHA, RESPONSABLE)
    assert muestra.estado == "Extraída"


# Remito: cadena de envío


def test_despacho_no_mueve_las_muestras_hasta_el_siguiente_tramo():
    remito = remito_con_muestras()
    remito.despachar(FECHA, RESPONSABLE)
    assert remito.estado == "Despachado"
    assert estados_de(remito) == {"Empaquetada"}
    remito.registrar_tramo(FECHA, RESPONSABLE)
    assert remito.estado == "En tránsito"
    assert estados_de(remito) == {"En tránsito"}


def test_tramos_siguientes_no_agregan_registros():
    remito = remito_en_transito()
    cantidad = len(remito.historial)
    remito.registrar_tramo(FECHA, RESPONSABLE)
    assert remito.estado == "En tránsito"
    assert len(remito.historial) == cantidad


def test_no_se_registra_un_tramo_antes_del_despacho():
    remito = remito_con_muestras()
    with pytest.raises(TransicionInvalida):
        remito.registrar_tramo(FECHA, RESPONSABLE)


def test_no_se_despacha_dos_veces():
    remito = remito_con_muestras()
    remito.despachar(FECHA, RESPONSABLE)
    with pytest.raises(TransicionInvalida):
        remito.despachar(FECHA, RESPONSABLE)


# Remito: recepción


def test_precinto_intacto_recibe_remito_y_muestras():
    remito = remito_en_transito()
    remito.registrar_recepcion("Intacto", FECHA, RESPONSABLE)
    assert remito.estado == "Recibido"
    assert estados_de(remito) == {"Recibida"}


def test_precinto_roto_rechaza_remito_y_todas_sus_muestras():
    remito = remito_en_transito()
    remito.registrar_recepcion("Roto", FECHA, RESPONSABLE, "Precinto cortado")
    assert remito.estado == "Rechazado"
    assert estados_de(remito) == {"Rechazada"}
    assert remito.historial[-1].observacion == "Precinto cortado"
    for muestra in remito.muestras:
        with pytest.raises(TransicionInvalida):
            muestra.analizar(FECHA, RESPONSABLE)


def test_precinto_con_valor_invalido_no_cambia_nada():
    remito = remito_en_transito()
    with pytest.raises(ValueError, match="precinto inválido"):
        remito.registrar_recepcion("Dudoso", FECHA, RESPONSABLE)
    assert remito.estado == "En tránsito"
    assert estados_de(remito) == {"En tránsito"}


@pytest.mark.parametrize("preparar", [crear_remito, remito_con_muestras])
def test_no_se_recibe_un_remito_que_no_salio(preparar):
    remito = preparar()
    with pytest.raises(TransicionInvalida):
        remito.registrar_recepcion("Intacto", FECHA, RESPONSABLE)


def test_no_se_recibe_un_remito_solo_despachado():
    remito = remito_con_muestras()
    remito.despachar(FECHA, RESPONSABLE)
    with pytest.raises(TransicionInvalida):
        remito.registrar_recepcion("Intacto", FECHA, RESPONSABLE)


@pytest.mark.parametrize("precinto", ["Intacto", "Roto"])
def test_remito_no_admite_operaciones_despues_de_la_recepcion(precinto):
    remito = remito_en_transito()
    remito.registrar_recepcion(precinto, FECHA, RESPONSABLE)
    with pytest.raises(TransicionInvalida):
        remito.registrar_recepcion("Intacto", FECHA, RESPONSABLE)
    with pytest.raises(TransicionInvalida):
        remito.registrar_tramo(FECHA, RESPONSABLE)
    with pytest.raises(TransicionInvalida):
        remito.despachar(FECHA, RESPONSABLE)


def test_muestra_desalineada_frena_la_recepcion_sin_cambios_parciales():
    remito = remito_en_transito()
    # Una muestra avanza por fuera del remito.
    remito.muestras[1].recibir(FECHA, RESPONSABLE)
    with pytest.raises(TransicionInvalida, match="M-1"):
        remito.registrar_recepcion("Roto", FECHA, RESPONSABLE)
    assert remito.estado == "En tránsito"
    assert remito.muestras[0].estado == "En tránsito"


def test_fecha_anterior_a_una_muestra_frena_el_tramo_sin_cambios_parciales():
    remito = crear_remito()
    remito.agregar_muestra(crear_muestra(), "2026-11-03 12:00", RESPONSABLE)
    remito.despachar("2026-11-03 11:00", RESPONSABLE)
    with pytest.raises(ValueError, match="M-1"):
        remito.registrar_tramo("2026-11-03 11:30", RESPONSABLE)
    assert remito.estado == "Despachado"
    assert estados_de(remito) == {"Empaquetada"}


def test_recorrido_completo_deja_el_historial_en_orden():
    muestra = Muestra("M-1", 1, 1, "2026-11-03 09:00", RESPONSABLE)
    remito = Remito("R-1", 1, 1, 1, "2026-11-03 10:00", RESPONSABLE)
    remito.agregar_muestra(muestra, "2026-11-03 10:00", RESPONSABLE)
    remito.despachar("2026-11-03 11:00", "Chofer")
    remito.registrar_tramo("2026-11-03 13:00", "Chofer")
    remito.registrar_recepcion("Intacto", "2026-11-03 15:00", "Bioquímica")
    muestra.analizar("2026-11-04 09:00", "Bioquímica")
    assert [r.estado for r in remito.historial] == ["Emitido", "Despachado", "En tránsito", "Recibido"]
    assert [r.estado for r in muestra.historial] == [
        "Extraída", "Empaquetada", "En tránsito", "Recibida", "Analizada",
    ]


# Coherencia con la base de datos


@pytest.mark.parametrize("nombre, clase", ESTADOS_MUESTRA.items())
def test_nombre_de_cada_estado_de_muestra_coincide_con_su_clave(nombre, clase):
    assert issubclass(clase, EstadoMuestra)
    assert clase().nombre == nombre


@pytest.mark.parametrize("nombre, clase", ESTADOS_REMITO.items())
def test_nombre_de_cada_estado_de_remito_coincide_con_su_clave(nombre, clase):
    assert issubclass(clase, EstadoRemito)
    assert clase().nombre == nombre


def test_todos_los_estados_cumplen_los_check_de_la_base():
    cx = conectar(":memory:")
    crear_tablas(cx)
    cargar_datos_ejemplo(cx)
    consulta_id = cx.execute(
        """INSERT INTO consultas (historia_id, veterinario_id, clinica_id, fecha_hora, tipo, precio)
           VALUES (1, 1, 1, ?, 'Urgencia', 1000)""",
        (FECHA,),
    ).lastrowid
    orden_id = cx.execute(
        "INSERT INTO ordenes_derivacion (consulta_id, laboratorio_id, fecha_emision) VALUES (?, 1, ?)",
        (consulta_id, FECHA),
    ).lastrowid
    muestra_id = cx.execute(
        "INSERT INTO muestras (orden_id, tipo_analisis_id, codigo, fecha_extraccion) VALUES (?, 1, 'M-1', ?)",
        (orden_id, FECHA),
    ).lastrowid
    remito_id = cx.execute(
        """INSERT INTO remitos_biologicos (numero, clinica_id, laboratorio_id, conservadora_id, fecha_emision)
           VALUES ('R-1', 1, 1, 1, ?)""",
        (FECHA,),
    ).lastrowid
    for nombre in ESTADOS_MUESTRA:
        cx.execute("UPDATE muestras SET estado_actual = ? WHERE id = ?", (nombre, muestra_id))
        cx.execute(
            "INSERT INTO historial_estados_muestra (muestra_id, estado, fecha_hora, responsable) VALUES (?, ?, ?, ?)",
            (muestra_id, nombre, FECHA, RESPONSABLE),
        )
    for nombre in ESTADOS_REMITO:
        cx.execute("UPDATE remitos_biologicos SET estado_actual = ? WHERE id = ?", (nombre, remito_id))
        cx.execute(
            "INSERT INTO historial_estados_remito (remito_id, estado, fecha_hora, responsable) VALUES (?, ?, ?, ?)",
            (remito_id, nombre, FECHA, RESPONSABLE),
        )
    cx.close()
