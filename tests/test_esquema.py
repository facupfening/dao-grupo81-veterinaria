import sqlite3

import pytest

from datos.base_datos import cargar_datos_ejemplo, conectar, crear_tablas, inicializar

TABLAS_DER = {
    "especies", "clientes", "clinicas", "veterinarios", "mascotas",
    "historias_clinicas", "vacunas", "turnos", "consultas", "aplicaciones_vacuna",
    "laboratorios", "tipos_analisis", "ordenes_derivacion", "conservadoras",
    "remitos_biologicos", "muestras", "historial_estados_muestra",
    "historial_estados_remito", "precintos", "transportistas", "eventos_envio",
    "recepciones", "resultados", "comprobantes", "detalles_comprobante",
}


@pytest.fixture
def conexion():
    """Base en memoria con los datos de ejemplo, nueva para cada prueba."""
    cx = conectar(":memory:")
    crear_tablas(cx)
    cargar_datos_ejemplo(cx)
    yield cx
    cx.close()


def crear_turno(cx, inicio, fin, veterinario_id=1, estado="Reservado"):
    cursor = cx.execute(
        "INSERT INTO turnos (mascota_id, veterinario_id, inicio, fin, estado) VALUES (1, ?, ?, ?, ?)",
        (veterinario_id, inicio, fin, estado),
    )
    return cursor.lastrowid


def crear_consulta(cx):
    cursor = cx.execute(
        """INSERT INTO consultas (historia_id, veterinario_id, clinica_id, fecha_hora, tipo, precio)
           VALUES (1, 1, 1, '2026-11-03 10:00', 'Urgencia', 20000)"""
    )
    return cursor.lastrowid


def crear_muestra(cx):
    consulta_id = crear_consulta(cx)
    orden_id = cx.execute(
        "INSERT INTO ordenes_derivacion (consulta_id, laboratorio_id, fecha_emision) VALUES (?, 1, '2026-11-03 10:30')",
        (consulta_id,),
    ).lastrowid
    return cx.execute(
        """INSERT INTO muestras (orden_id, tipo_analisis_id, codigo, fecha_extraccion)
           VALUES (?, 1, 'M-0001', '2026-11-03 10:15')""",
        (orden_id,),
    ).lastrowid


def crear_remito(cx):
    return cx.execute(
        """INSERT INTO remitos_biologicos (numero, clinica_id, laboratorio_id, conservadora_id, fecha_emision)
           VALUES ('R-0001', 1, 1, 1, '2026-11-03 11:00')"""
    ).lastrowid


# Estructura


def test_estan_las_25_tablas_del_der(conexion):
    filas = conexion.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    assert {fila["name"] for fila in filas} == TABLAS_DER


def test_inicializar_dos_veces_no_duplica_datos(tmp_path):
    ruta = tmp_path / "prueba.db"
    inicializar(ruta)
    inicializar(ruta)
    cx = conectar(ruta)
    assert cx.execute("SELECT COUNT(*) FROM especies").fetchone()[0] == 2
    cx.close()


def test_los_textos_con_acento_se_cargan_bien(conexion):
    fila = conexion.execute("SELECT nombre FROM vacunas WHERE id = 1").fetchone()
    assert fila["nombre"] == "Antirrábica"


def test_cada_mascota_de_ejemplo_tiene_historia_clinica(conexion):
    sin_historia = conexion.execute(
        """SELECT COUNT(*) FROM mascotas m
           LEFT JOIN historias_clinicas h ON h.mascota_id = m.id
           WHERE h.id IS NULL"""
    ).fetchone()[0]
    assert sin_historia == 0


# Restricciones


def test_mascota_sin_responsable_es_rechazada(conexion):
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute("INSERT INTO mascotas (especie_id, nombre) VALUES (1, 'Sin dueño')")


def test_mascota_con_responsable_inexistente_es_rechazada(conexion):
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute("INSERT INTO mascotas (cliente_id, especie_id, nombre) VALUES (999, 1, 'Fantasma')")


def test_dni_repetido_es_rechazado(conexion):
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute("INSERT INTO clientes (dni, nombre, apellido) VALUES ('30000001', 'Otra', 'Persona')")


def test_cliente_con_mascotas_no_se_puede_borrar(conexion):
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute("DELETE FROM clientes WHERE id = 1")


def test_muestra_nace_extraida_y_sin_remito(conexion):
    muestra_id = crear_muestra(conexion)
    fila = conexion.execute("SELECT estado_actual, remito_id FROM muestras WHERE id = ?", (muestra_id,)).fetchone()
    assert fila["estado_actual"] == "Extraída"
    assert fila["remito_id"] is None


def test_remito_nace_emitido(conexion):
    remito_id = crear_remito(conexion)
    fila = conexion.execute("SELECT estado_actual FROM remitos_biologicos WHERE id = ?", (remito_id,)).fetchone()
    assert fila["estado_actual"] == "Emitido"


def test_consulta_sin_turno_esta_permitida(conexion):
    consulta_id = crear_consulta(conexion)
    fila = conexion.execute("SELECT turno_id FROM consultas WHERE id = ?", (consulta_id,)).fetchone()
    assert fila["turno_id"] is None


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE consultas SET tipo = 'Cirugía'",
        "UPDATE muestras SET estado_actual = 'Perdida'",
        "UPDATE remitos_biologicos SET estado_actual = 'Perdido'",
        "UPDATE ordenes_derivacion SET prioridad = 'Baja'",
        "UPDATE conservadoras SET estado = 'Rota'",
    ],
)
def test_valores_fuera_del_check_son_rechazados(conexion, sql):
    crear_muestra(conexion)
    crear_remito(conexion)
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(sql)


def test_recepcion_con_estado_de_precinto_invalido_es_rechazada(conexion):
    remito_id = crear_remito(conexion)
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            """INSERT INTO recepciones (remito_id, fecha_hora, recibido_por, estado_precinto, temp_llegada)
               VALUES (?, '2026-11-03 15:00', 'Bioquímica', 'Dudoso', 5)""",
            (remito_id,),
        )


def test_remito_admite_una_sola_recepcion_y_un_solo_precinto(conexion):
    remito_id = crear_remito(conexion)
    sql_recepcion = """INSERT INTO recepciones (remito_id, fecha_hora, recibido_por, estado_precinto, temp_llegada)
                       VALUES (?, '2026-11-03 15:00', 'Bioquímica', 'Intacto', 5)"""
    sql_precinto = """INSERT INTO precintos (remito_id, numero, fecha_colocacion, colocado_por)
                      VALUES (?, ?, '2026-11-03 11:00', 'Laura Gómez')"""
    conexion.execute(sql_recepcion, (remito_id,))
    conexion.execute(sql_precinto, (remito_id, "P-1"))
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(sql_recepcion, (remito_id,))
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(sql_precinto, (remito_id, "P-2"))


@pytest.mark.parametrize("consulta, muestra", [(False, False), (True, True)])
def test_detalle_debe_ser_de_consulta_o_de_muestra(conexion, consulta, muestra):
    consulta_id = crear_consulta(conexion) if consulta else None
    muestra_id = crear_muestra(conexion) if muestra else None
    comprobante_id = conexion.execute(
        "INSERT INTO comprobantes (numero, cliente_id, clinica_id, fecha, total) VALUES ('C-1', 1, 1, '2026-11-03', 0)"
    ).lastrowid
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            """INSERT INTO detalles_comprobante
               (comprobante_id, consulta_id, muestra_id, descripcion, cantidad, precio_unitario)
               VALUES (?, ?, ?, 'Servicio', 1, 100)""",
            (comprobante_id, consulta_id, muestra_id),
        )


# Historiales inmutables


def historial_de_muestra(cx):
    muestra_id = crear_muestra(cx)
    cx.execute(
        """INSERT INTO historial_estados_muestra (muestra_id, estado, fecha_hora, responsable)
           VALUES (?, 'Extraída', '2026-11-03 10:15', 'Laura Gómez')""",
        (muestra_id,),
    )
    return "historial_estados_muestra"


def historial_de_remito(cx):
    remito_id = crear_remito(cx)
    cx.execute(
        """INSERT INTO historial_estados_remito (remito_id, estado, fecha_hora, responsable)
           VALUES (?, 'Emitido', '2026-11-03 11:00', 'Laura Gómez')""",
        (remito_id,),
    )
    return "historial_estados_remito"


@pytest.mark.parametrize("preparar", [historial_de_muestra, historial_de_remito])
def test_historial_no_se_puede_modificar(conexion, preparar):
    tabla = preparar(conexion)
    with pytest.raises(sqlite3.IntegrityError, match="no se puede modificar"):
        conexion.execute(f"UPDATE {tabla} SET responsable = 'Otra persona'")


@pytest.mark.parametrize("preparar", [historial_de_muestra, historial_de_remito])
def test_historial_no_se_puede_borrar(conexion, preparar):
    tabla = preparar(conexion)
    with pytest.raises(sqlite3.IntegrityError, match="no se puede borrar"):
        conexion.execute(f"DELETE FROM {tabla}")


@pytest.mark.parametrize("preparar", [historial_de_muestra, historial_de_remito])
def test_historial_admite_nuevas_inserciones(conexion, preparar):
    tabla = preparar(conexion)
    columna = "muestra_id" if tabla == "historial_estados_muestra" else "remito_id"
    estado = "Rechazada" if tabla == "historial_estados_muestra" else "Rechazado"
    conexion.execute(
        f"INSERT INTO {tabla} ({columna}, estado, fecha_hora, responsable) VALUES (1, ?, '2026-11-03 15:00', 'Bioquímica')",
        (estado,),
    )
    assert conexion.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0] == 2


# Agenda de turnos


@pytest.mark.parametrize(
    "inicio, fin",
    [
        ("2026-11-03 10:00", "2026-11-03 10:30"),  # mismo horario
        ("2026-11-03 09:45", "2026-11-03 10:15"),  # pisa el comienzo
        ("2026-11-03 10:15", "2026-11-03 10:45"),  # pisa el final
        ("2026-11-03 10:10", "2026-11-03 10:20"),  # queda adentro
        ("2026-11-03 09:00", "2026-11-03 11:00"),  # lo envuelve
    ],
)
def test_turno_superpuesto_es_rechazado(conexion, inicio, fin):
    crear_turno(conexion, "2026-11-03 10:00", "2026-11-03 10:30")
    with pytest.raises(sqlite3.IntegrityError, match="ya tiene un turno"):
        crear_turno(conexion, inicio, fin)


@pytest.mark.parametrize(
    "inicio, fin",
    [
        ("2026-11-03 09:30", "2026-11-03 10:00"),  # termina justo cuando empieza el otro
        ("2026-11-03 10:30", "2026-11-03 11:00"),  # empieza justo cuando termina el otro
    ],
)
def test_turnos_contiguos_estan_permitidos(conexion, inicio, fin):
    crear_turno(conexion, "2026-11-03 10:00", "2026-11-03 10:30")
    assert crear_turno(conexion, inicio, fin) > 0


def test_turno_sin_estado_explicito_tambien_se_controla(conexion):
    crear_turno(conexion, "2026-11-03 10:00", "2026-11-03 10:30")
    with pytest.raises(sqlite3.IntegrityError, match="ya tiene un turno"):
        conexion.execute(
            """INSERT INTO turnos (mascota_id, veterinario_id, inicio, fin)
               VALUES (1, 1, '2026-11-03 10:00', '2026-11-03 10:30')"""
        )


def test_otro_veterinario_puede_tener_el_mismo_horario(conexion):
    crear_turno(conexion, "2026-11-03 10:00", "2026-11-03 10:30")
    assert crear_turno(conexion, "2026-11-03 10:00", "2026-11-03 10:30", veterinario_id=2) > 0


def test_turno_cancelado_libera_el_horario(conexion):
    turno_id = crear_turno(conexion, "2026-11-03 10:00", "2026-11-03 10:30")
    conexion.execute("UPDATE turnos SET estado = 'Cancelado' WHERE id = ?", (turno_id,))
    assert crear_turno(conexion, "2026-11-03 10:00", "2026-11-03 10:30") > 0


def test_no_se_puede_reactivar_un_turno_si_el_horario_se_ocupo(conexion):
    turno_id = crear_turno(conexion, "2026-11-03 10:00", "2026-11-03 10:30", estado="Cancelado")
    crear_turno(conexion, "2026-11-03 10:00", "2026-11-03 10:30")
    with pytest.raises(sqlite3.IntegrityError, match="ya tiene un turno"):
        conexion.execute("UPDATE turnos SET estado = 'Reservado' WHERE id = ?", (turno_id,))


def test_mover_un_turno_sobre_otro_es_rechazado(conexion):
    crear_turno(conexion, "2026-11-03 10:00", "2026-11-03 10:30")
    turno_id = crear_turno(conexion, "2026-11-03 11:00", "2026-11-03 11:30")
    with pytest.raises(sqlite3.IntegrityError, match="ya tiene un turno"):
        conexion.execute(
            "UPDATE turnos SET inicio = '2026-11-03 10:15', fin = '2026-11-03 10:45' WHERE id = ?",
            (turno_id,),
        )


def test_un_turno_se_puede_correr_sobre_su_propio_horario(conexion):
    turno_id = crear_turno(conexion, "2026-11-03 10:00", "2026-11-03 10:30")
    conexion.execute("UPDATE turnos SET fin = '2026-11-03 10:45' WHERE id = ?", (turno_id,))
    fila = conexion.execute("SELECT fin FROM turnos WHERE id = ?", (turno_id,)).fetchone()
    assert fila["fin"] == "2026-11-03 10:45"


def test_turno_con_fin_anterior_al_inicio_es_rechazado(conexion):
    with pytest.raises(sqlite3.IntegrityError):
        crear_turno(conexion, "2026-11-03 10:30", "2026-11-03 10:00")
