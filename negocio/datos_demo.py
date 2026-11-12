"""Atenciones ficticias para demostrar el sistema: 25 consultas que recorren todas las opciones.

Se cargan con los mismos gestores que usa la aplicación, de modo que los
historiales de estado y las reglas del negocio se cumplen igual que en el uso real.

Qué queda cargado:
- 10 clientes y 13 mascotas (perros y gatos), en las 3 clínicas y con los 4 veterinarios.
- Consultas de los 3 tipos (Consulta, Control, Urgencia), entre septiembre de 2025 y noviembre de 2026.
- Turnos Atendidos, Cancelados y Reservados.
- Vacunas al día, vencidas y faltantes, incluidas algunas no obligatorias.
- Muestras en los 6 estados y remitos en los 5 estados, con los 6 tipos de análisis y los 2 laboratorios.
- Precintos intactos y rotos, traspasos entre transportistas y órdenes Normales y Urgentes.
- Conservadoras Disponibles, En uso y Fuera de servicio.
- Comprobantes con consulta sola, con consulta y análisis, y uno emitido antes de tener los análisis.
"""

from datetime import datetime, timedelta

from modelos.validaciones import FORMATO_FECHA_HORA
from negocio.gestor_atencion import GestorAtencion
from negocio.gestor_clientes import GestorClientes
from negocio.gestor_envios import GestorEnvios
from negocio.gestor_laboratorio import GestorLaboratorio
from negocio.gestor_mascotas import GestorMascotas

PERRO, GATO = 1, 2
GOMEZ, FERREYRA, RIOS, ACOSTA = 1, 2, 3, 4  # Gómez y Ferreyra: Centro; Ríos: Norte; Acosta: Sur
HEMOGRAMA, BIOQUIMICO, URIANALISIS, COPROPARASITOLOGICO, HISTOPATOLOGIA, PCR = 1, 2, 3, 4, 5, 6
ANTIRRABICA_PERRO, SEXTUPLE, TOS_PERRERAS, ANTIRRABICA_GATO, TRIPLE_FELINA, LEUCEMIA_FELINA = 1, 2, 3, 4, 5, 6
REF_01, REF_02, AMB_01, CON_01 = 1, 2, 3, 4  # heladeras (2 a 8 °C), ambiente (15 a 25 °C) y freezer (-20 a -10 °C)
TRANSPORTE_EJEMPLO, LOGISTICA_FICTICIA, ENVIOS_DEL_CENTRO = 1, 2, 3
CENTRAL, DEL_SUR = 1, 2  # laboratorios
RESPONSABLE = "Personal de clínica"
BIOQUIMICA = "Bioq. Marina Vega"

# Clientes nuevos: (dni, nombre, apellido, teléfono, email, dirección). Los 3 primeros ya vienen en datos_ejemplo.sql.
CLIENTES = [
    ("32000004", "Rodrigo", "Pereyra", "351-100-0004", "rodrigo@example.com", "Calle Cuatro 444"),
    ("33000005", "Valeria", "Domínguez", "351-100-0005", None, "Calle Cinco 555"),
    ("34000006", "Martín", "Herrera", "351-100-0006", "martin@example.com", None),
    ("35000007", "Camila", "Torres", None, "camila@example.com", "Calle Siete 777"),
    ("36000008", "Lucas", "Fernández", "351-100-0008", "lucas@example.com", "Calle Ocho 888"),
    ("37000009", "Sofía", "Castro", "351-100-0009", None, None),
    ("38000010", "Gabriel", "Medina", "351-100-0010", "gabriel@example.com", "Calle Diez 1010"),
]

# Mascotas nuevas: (DNI del dueño, especie, nombre, raza, sexo, nacimiento, peso, antecedentes).
MASCOTAS = [
    ("32000004", PERRO, "Rocco", "Bulldog francés", "Macho", "2020-05-10", 12.3, "Piel sensible"),
    ("32000004", PERRO, "Kira", "Ovejero alemán", "Hembra", "2018-08-22", 30.1, None),
    ("33000005", GATO, "Michi", "Persa", "Hembra", "2021-12-01", 4.0, None),
    ("34000006", PERRO, "Bruno", "Beagle", "Macho", "2022-02-14", 11.5, "Estómago delicado"),
    ("35000007", GATO, "Nala", "Común europeo", "Hembra", "2024-04-03", 3.1, None),
    ("36000008", PERRO, "Thor", "Golden retriever", "Macho", "2017-06-30", 33.0, "Operado de rodilla"),
    ("37000009", PERRO, "Lola", None, "Hembra", "2023-09-09", 9.4, None),
    ("38000010", GATO, "Felix", "Siamés", "Macho", "2020-10-10", 5.2, None),
    ("38000010", PERRO, "Coco", "Caniche toy", "Macho", "2025-01-20", None, None),
]


def _texto(fecha):
    return fecha.strftime(FORMATO_FECHA_HORA)


class CargaDemo:
    def __init__(self, ruta):
        self.atencion = GestorAtencion(ruta)
        self.envios = GestorEnvios(ruta)
        self.laboratorio = GestorLaboratorio(ruta)
        self.clientes = GestorClientes(ruta)
        self.mascotas = GestorMascotas(ruta)
        # Nombre de la mascota -> id. Las 4 primeras vienen en datos_ejemplo.sql.
        self.mascota = {"Toby": 1, "Mora": 2, "Luna": 3, "Simón": 4}

    def cargar(self):
        """Devuelve False si la base ya tiene consultas, para no mezclar datos."""
        if self.atencion.listar_consultas():
            return False
        self._clientes_y_mascotas()
        self._consultas_sin_laboratorio()
        self._vacunas()
        self._analisis_completos()
        self._muestras_rechazadas()
        self._turnos()
        # Al final, las muestras que quedan a mitad de camino: sus conservadoras quedan En uso.
        self._muestras_por_analizar()
        self._muestras_en_camino()
        self._muestras_sin_empaquetar()
        return True

    # Clientes y mascotas

    def _clientes_y_mascotas(self):
        ids_clientes = {}
        for dni, nombre, apellido, telefono, email, direccion in CLIENTES:
            ids_clientes[dni] = self.clientes.alta(dni, nombre, apellido, telefono, email, direccion)
        for dni, especie, nombre, raza, sexo, nacimiento, peso, antecedentes in MASCOTAS:
            self.mascota[nombre] = self.mascotas.alta(ids_clientes[dni], especie, nombre, "2025-08-01 09:00",
                                                      raza, sexo, nacimiento, peso, antecedentes)

    # Consultas

    def _consultas_sin_laboratorio(self):
        consulta = self._consulta("Thor", GOMEZ, datetime(2026, 8, 25, 18, 30), "Urgencia", 30000,
                                  "Herida en la pata", "Laceración", "Sutura y antibiótico")
        self.laboratorio.emitir_comprobante(consulta, "2026-08-25 19:30")
        consulta = self._consulta("Coco", ACOSTA, datetime(2026, 11, 2, 10, 0), "Control", 12000,
                                  "Primera visita", "Cachorro sano", "Plan de vacunación", con_turno=True)
        self.laboratorio.emitir_comprobante(consulta, "2026-11-02 10:30")

    def _vacunas(self):
        """Dosis vencidas (aplicadas hace más de un año), al día, incompletas y no obligatorias."""
        self._consulta("Luna", RIOS, datetime(2025, 9, 1, 10, 0), "Control", 15000, "Control anual", "Sana",
                       "Sin indicaciones", vacunas=[(ANTIRRABICA_PERRO, "L-2025-1")])
        consulta = self._consulta("Thor", ACOSTA, datetime(2025, 10, 3, 11, 0), "Control", 15000, "Vacunación",
                                  "Sano", None, vacunas=[(ANTIRRABICA_PERRO, "L-2025-4"), (SEXTUPLE, "L-2025-5")])
        self.laboratorio.emitir_comprobante(consulta, "2025-10-03 11:30")
        consulta = self._consulta("Rocco", GOMEZ, datetime(2026, 1, 15, 9, 0), "Consulta", 20000, "Picazón",
                                  "Dermatitis alérgica", "Antihistamínico por 10 días", con_turno=True,
                                  vacunas=[(ANTIRRABICA_PERRO, "L-2026-1"), (SEXTUPLE, "L-2026-2"),
                                           (TOS_PERRERAS, "L-2026-3")])
        self.laboratorio.emitir_comprobante(consulta, "2026-01-15 09:45")
        consulta = self._consulta("Bruno", FERREYRA, datetime(2026, 6, 18, 17, 0), "Control", 15000, "Vacunación",
                                  "Sano", "Falta la antirrábica", vacunas=[(SEXTUPLE, "L-2026-4")])
        self.laboratorio.emitir_comprobante(consulta, "2026-06-18 17:30")
        consulta = self._consulta("Nala", ACOSTA, datetime(2026, 8, 12, 12, 0), "Control", 15000, "Vacunación",
                                  "Sana", None, vacunas=[(ANTIRRABICA_GATO, "L-2026-5"), (TRIPLE_FELINA, "L-2026-6"),
                                                         (LEUCEMIA_FELINA, "L-2026-7")])
        self.laboratorio.emitir_comprobante(consulta, "2026-08-12 12:30")
        consulta = self._consulta("Kira", RIOS, datetime(2026, 9, 15, 15, 0), "Control", 15000, "Vacunación",
                                  "Sana", None, vacunas=[(ANTIRRABICA_PERRO, "L-2026-8"), (SEXTUPLE, "L-2026-9")])
        self.laboratorio.emitir_comprobante(consulta, "2026-09-15 15:30")
        consulta = self._consulta("Mora", FERREYRA, datetime(2026, 10, 8, 11, 0), "Control", 15000, "Vacunación",
                                  "Sana", None, vacunas=[(ANTIRRABICA_GATO, "L-2026-10"), (TRIPLE_FELINA, "L-2026-11")])
        self.laboratorio.emitir_comprobante(consulta, "2026-10-08 11:30")

    def _analisis_completos(self):
        """Muestras que llegaron bien y ya tienen resultado. Cambian el tiempo de viaje y de análisis."""
        consulta = self._consulta("Kira", RIOS, datetime(2026, 3, 10, 10, 0), "Consulta", 22000, "Cojera",
                                  "Displasia de cadera", "Antiinflamatorio y reposo")
        muestras = self._derivar(consulta, datetime(2026, 3, 10, 10, 0), [HEMOGRAMA, BIOQUIMICO], REF_02,
                                 [TRANSPORTE_EJEMPLO], "Intacto", horas_de_viaje=4)
        self._analizar(muestras, datetime(2026, 3, 11, 12, 0), ["Hto 41%", "Urea 38 mg/dL"])
        self.laboratorio.emitir_comprobante(consulta, "2026-03-11 18:00")

        consulta = self._consulta("Michi", ACOSTA, datetime(2026, 5, 6, 21, 0), "Urgencia", 30000, "No come",
                                  "Lipidosis hepática", "Alimentación asistida")
        muestras = self._derivar(consulta, datetime(2026, 5, 6, 21, 0), [BIOQUIMICO, URIANALISIS], REF_01,
                                 [ENVIOS_DEL_CENTRO], "Intacto", horas_de_viaje=2, laboratorio=DEL_SUR,
                                 prioridad="Urgente")
        self._analizar(muestras, datetime(2026, 5, 7, 5, 0), ["ALT 180 U/L", "Densidad 1.030"])
        self.laboratorio.emitir_comprobante(consulta, "2026-05-07 10:00")

        consulta = self._consulta("Felix", RIOS, datetime(2026, 7, 22, 16, 0), "Consulta", 20000, "Estornudos",
                                  "Sospecha de virus respiratorio", "Antibiótico por 7 días")
        muestras = self._derivar(consulta, datetime(2026, 7, 22, 16, 0), [PCR], CON_01, [LOGISTICA_FICTICIA],
                                 "Intacto", horas_de_viaje=5, temperatura=-15)
        self._analizar(muestras, datetime(2026, 7, 25, 11, 0), ["Calicivirus negativo"])
        self.laboratorio.emitir_comprobante(consulta, "2026-07-25 18:00")

        consulta = self._consulta("Toby", GOMEZ, datetime(2026, 10, 5, 9, 5), "Consulta", 20000, "Decaimiento",
                                  "Anemia leve", "Suplemento de hierro por 30 días", con_turno=True,
                                  vacunas=[(ANTIRRABICA_PERRO, "L-2026-14")])
        muestras = self._derivar(consulta, datetime(2026, 10, 5, 9, 5), [HEMOGRAMA, BIOQUIMICO], REF_01,
                                 [TRANSPORTE_EJEMPLO], "Intacto", horas_de_viaje=3)
        self._analizar(muestras, datetime(2026, 10, 6, 9, 0), ["Hto 32%", "Glucosa 92 mg/dL"])
        self.laboratorio.emitir_comprobante(consulta, "2026-10-06 18:00")

        consulta = self._consulta("Simón", RIOS, datetime(2026, 10, 15, 10, 0), "Consulta", 22000,
                                  "Nódulo en el lomo", "Nódulo a estudiar", "Control en 15 días")
        muestras = self._derivar(consulta, datetime(2026, 10, 15, 10, 0), [HISTOPATOLOGIA], AMB_01,
                                 [LOGISTICA_FICTICIA], "Intacto", horas_de_viaje=6, temperatura=20)
        self._analizar(muestras, datetime(2026, 10, 19, 15, 0), ["Lipoma benigno"])
        self.laboratorio.emitir_comprobante(consulta, "2026-10-19 18:00")

    def _muestras_rechazadas(self):
        """El precinto llegó roto: el remito y sus muestras se rechazan y no se facturan."""
        consulta = self._consulta("Lola", ACOSTA, datetime(2026, 9, 9, 9, 30), "Consulta", 20000, "Diarrea",
                                  "Parasitosis", "Antiparasitario")
        self._derivar(consulta, datetime(2026, 9, 9, 9, 30), [COPROPARASITOLOGICO], REF_02,
                      [ENVIOS_DEL_CENTRO, TRANSPORTE_EJEMPLO], "Roto", horas_de_viaje=7)
        self.laboratorio.emitir_comprobante(consulta, "2026-09-09 18:00")

        consulta = self._consulta("Rocco", FERREYRA, datetime(2026, 9, 30, 14, 0), "Consulta", 20000, "Otitis",
                                  "Otitis externa", "Gotas óticas")
        self._derivar(consulta, datetime(2026, 9, 30, 14, 0), [HEMOGRAMA], REF_01, [LOGISTICA_FICTICIA], "Roto",
                      horas_de_viaje=3)
        self.laboratorio.emitir_comprobante(consulta, "2026-09-30 19:00")

        consulta = self._consulta("Luna", RIOS, datetime(2026, 10, 12, 22, 0), "Urgencia", 30000, "Vómitos",
                                  "Infección urinaria", "Antibiótico por 7 días")
        self._derivar(consulta, datetime(2026, 10, 12, 22, 0), [URIANALISIS], REF_02, [LOGISTICA_FICTICIA], "Roto",
                      horas_de_viaje=5)
        self.laboratorio.emitir_comprobante(consulta, "2026-10-13 10:00")

        consulta = self._consulta("Toby", FERREYRA, datetime(2026, 10, 20, 8, 0), "Urgencia", 30000, "Diarrea",
                                  "Gastroenteritis", "Dieta blanda y probióticos")
        self._derivar(consulta, datetime(2026, 10, 20, 8, 0), [COPROPARASITOLOGICO, HEMOGRAMA], REF_01,
                      [TRANSPORTE_EJEMPLO, LOGISTICA_FICTICIA], "Roto", horas_de_viaje=4)
        self.laboratorio.emitir_comprobante(consulta, "2026-10-20 18:00")

    def _turnos(self):
        """Un turno cancelado y dos reservados para los próximos días."""
        turno = self.atencion.reservar_turno(self.mascota["Bruno"], GOMEZ, "2026-11-03 10:00", "2026-11-03 10:30")
        self.atencion.cancelar_turno(turno)
        self.atencion.reservar_turno(self.mascota["Kira"], RIOS, "2026-11-16 09:00", "2026-11-16 09:30")
        self.atencion.reservar_turno(self.mascota["Nala"], ACOSTA, "2026-11-18 17:00", "2026-11-18 17:30")

    def _muestras_por_analizar(self):
        """Recibidas en el laboratorio y sin resultado: para cargarlo desde la pantalla de Laboratorio."""
        consulta = self._consulta("Mora", GOMEZ, datetime(2026, 10, 28, 16, 0), "Consulta", 20000,
                                  "Pérdida de peso", "A estudiar", "Dieta de recuperación")
        self._derivar(consulta, datetime(2026, 10, 28, 16, 0), [BIOQUIMICO], REF_02, [TRANSPORTE_EJEMPLO], "Intacto",
                      horas_de_viaje=2)
        consulta = self._consulta("Michi", ACOSTA, datetime(2026, 11, 4, 11, 0), "Control", 15000,
                                  "Control post lipidosis", "Recuperada", "Alta")
        self._derivar(consulta, datetime(2026, 11, 4, 11, 0), [HEMOGRAMA], REF_01, [ENVIOS_DEL_CENTRO], "Intacto",
                      horas_de_viaje=3, laboratorio=DEL_SUR)

    def _muestras_en_camino(self):
        """Un remito en cada estado intermedio: En tránsito, Despachado y Emitido."""
        # En tránsito (ya arribó, falta la recepción). La consulta se factura ya; los análisis, cuando terminen.
        fecha = datetime(2026, 11, 6, 10, 0)
        consulta = self._consulta("Bruno", GOMEZ, fecha, "Consulta", 20000, "Vómitos", "Gastritis",
                                  "Protector gástrico")
        muestras = self._ordenar(consulta, fecha, [BIOQUIMICO, URIANALISIS])
        remito = self._empaquetar(muestras, REF_02, fecha)
        self._despachar(remito, TRANSPORTE_EJEMPLO, fecha, 5)
        self._viajar(remito, [TRANSPORTE_EJEMPLO], fecha, 3, 6)
        self.laboratorio.emitir_comprobante(consulta, "2026-11-06 11:00")

        # Despachado (salió de la clínica). Sus muestras siguen Empaquetadas hasta el próximo tramo.
        fecha = datetime(2026, 11, 9, 20, 0)
        consulta = self._consulta("Felix", RIOS, fecha, "Urgencia", 30000, "Fiebre", "Infección viral", "Antivirales")
        muestras = self._ordenar(consulta, fecha, [PCR], prioridad="Urgente")
        remito = self._empaquetar(muestras, CON_01, fecha)
        self._despachar(remito, LOGISTICA_FICTICIA, fecha, -15)

        # Emitido (empaquetado, todavía en la clínica).
        fecha = datetime(2026, 11, 10, 12, 0)
        consulta = self._consulta("Thor", ACOSTA, fecha, "Consulta", 22000, "Bulto en el cuello", "Nódulo",
                                  "Biopsia")
        self._empaquetar(self._ordenar(consulta, fecha, [HISTOPATOLOGIA]), AMB_01, fecha)

    def _muestras_sin_empaquetar(self):
        """Extraídas: para probar el empaquetado desde la pantalla (REF-01 queda Disponible)."""
        fecha = datetime(2026, 11, 11, 9, 0)
        consulta = self._consulta("Lola", ACOSTA, fecha, "Control", 15000, "Vacunación y control", "Sana", None,
                                  vacunas=[(ANTIRRABICA_PERRO, "L-2026-12"), (SEXTUPLE, "L-2026-13")])
        self._ordenar(consulta, fecha, [HEMOGRAMA])
        fecha = datetime(2026, 11, 11, 15, 0)
        consulta = self._consulta("Rocco", GOMEZ, fecha, "Consulta", 20000, "Control de dermatitis", "En mejoría",
                                  "Seguir con antihistamínico")
        self._ordenar(consulta, fecha, [BIOQUIMICO])

    # Pasos que se repiten

    def _consulta(self, mascota, veterinario, fecha, tipo, precio, motivo, diagnostico, tratamiento,
                  con_turno=False, vacunas=()):
        """Registra la consulta y devuelve su id. Con turno, primero lo reserva y la consulta lo marca Atendido."""
        mascota_id = self.mascota[mascota]
        turno = None
        if con_turno:
            inicio = fecha - timedelta(minutes=5)
            turno = self.atencion.reservar_turno(mascota_id, veterinario, _texto(inicio),
                                                 _texto(inicio + timedelta(minutes=30)))
        return self.atencion.registrar_consulta(mascota_id, veterinario, _texto(fecha), tipo, precio, motivo,
                                                diagnostico, tratamiento, turno, vacunas)["consulta_id"]

    def _derivar(self, consulta, fecha, tipos, conservadora, transportistas, precinto, horas_de_viaje,
                 laboratorio=CENTRAL, prioridad="Normal", temperatura=5):
        """Lleva las muestras desde la extracción hasta la recepción y devuelve sus ids."""
        muestras = self._ordenar(consulta, fecha, tipos, laboratorio, prioridad)
        remito = self._empaquetar(muestras, conservadora, fecha)
        self._despachar(remito, transportistas[0], fecha, temperatura)
        llegada = self._viajar(remito, transportistas, fecha, horas_de_viaje, temperatura)
        observacion = "Precinto cortado" if precinto == "Roto" else None
        self.envios.registrar_recepcion(remito, precinto, _texto(llegada), BIOQUIMICA, temperatura, observacion)
        return muestras

    def _ordenar(self, consulta, fecha, tipos, laboratorio=CENTRAL, prioridad="Normal"):
        """Emite la orden: las muestras se extraen 10 minutos después de la consulta. Devuelve sus ids."""
        extraccion = fecha + timedelta(minutes=10)
        codigos = self.atencion.emitir_orden(
            consulta, laboratorio, _texto(extraccion + timedelta(minutes=5)),
            [(tipo, _texto(extraccion)) for tipo in tipos], RESPONSABLE, prioridad,
        )["codigos"]
        return [m["id"] for m in self.envios.listar_muestras_para_empaquetar() if m["codigo"] in codigos]

    def _empaquetar(self, muestras, conservadora, fecha):
        return self.envios.empaquetar(muestras, conservadora, _texto(fecha + timedelta(minutes=30)),
                                      RESPONSABLE)["remito_id"]

    def _despachar(self, remito, transportista, fecha, temperatura):
        self.envios.registrar_evento(remito, transportista, "Despacho", _texto(fecha + timedelta(hours=1)),
                                     "Clínica de origen", temperatura, "Chofer de salida")

    def _viajar(self, remito, transportistas, fecha, horas_de_viaje, temperatura):
        """Un traspaso por cada transportista extra y el arribo al laboratorio. Devuelve la hora de llegada."""
        despacho = fecha + timedelta(hours=1)
        for transportista in transportistas[1:]:
            self.envios.registrar_evento(remito, transportista, "Traspaso", _texto(despacho + timedelta(hours=1)),
                                         "Depósito intermedio", temperatura, "Chofer de relevo")
        llegada = despacho + timedelta(hours=horas_de_viaje)
        self.envios.registrar_evento(remito, transportistas[-1], "Arribo", _texto(llegada), "Laboratorio",
                                     temperatura, "Chofer de llegada")
        return llegada

    def _analizar(self, muestras, fecha, valores):
        for muestra, valor in zip(muestras, valores):
            self.laboratorio.registrar_resultado(muestra, _texto(fecha), BIOQUIMICA, valor, "Informado")
