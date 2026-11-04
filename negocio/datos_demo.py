"""Atenciones ficticias para demostrar el sistema.

Se cargan con los mismos gestores que usa la aplicación, de modo que los
historiales de estado y las reglas del negocio se cumplen igual que en el uso real.
"""

from datetime import datetime, timedelta

from modelos.validaciones import FORMATO_FECHA_HORA
from negocio.gestor_atencion import GestorAtencion
from negocio.gestor_envios import GestorEnvios
from negocio.gestor_laboratorio import GestorLaboratorio

TOBY, MORA, LUNA, SIMON = 1, 2, 3, 4
GOMEZ, FERREYRA, RIOS = 1, 2, 3
HEMOGRAMA, BIOQUIMICO, URIANALISIS, COPROPARASITOLOGICO, HISTOPATOLOGIA = 1, 2, 3, 4, 5
ANTIRRABICA_PERRO, SEXTUPLE, ANTIRRABICA_GATO, TRIPLE_FELINA = 1, 2, 4, 5
REF_01, REF_02, AMB_01 = 1, 2, 3
TRANSPORTE_EJEMPLO, LOGISTICA_FICTICIA = 1, 2
LABORATORIO = 1
RESPONSABLE = "Personal de clínica"
BIOQUIMICA = "Bioq. Marina Vega"


def _texto(fecha):
    return fecha.strftime(FORMATO_FECHA_HORA)


class CargaDemo:
    def __init__(self, ruta):
        self.atencion = GestorAtencion(ruta)
        self.envios = GestorEnvios(ruta)
        self.laboratorio = GestorLaboratorio(ruta)

    def cargar(self):
        """Devuelve False si la base ya tiene consultas, para no mezclar datos."""
        if self.atencion.listar_consultas():
            return False
        self._vacuna_antigua()
        self._consulta_con_analisis_recibidos()
        self._control_con_vacunas()
        self._urgencia_con_precinto_roto()
        self._biopsia_recibida()
        self._urgencia_con_traspaso_y_precinto_roto()
        self._consulta_con_analisis_por_informar()
        return True

    def _vacuna_antigua(self):
        """La dosis venció antes de hoy: aparece como vencida en el reporte de vacunas."""
        self.atencion.registrar_consulta(LUNA, RIOS, "2025-09-01 10:00", "Control", 15000, "Control anual",
                                         "Sana", "Sin indicaciones", vacunas=[(ANTIRRABICA_PERRO, "L-2025-1")])

    def _consulta_con_analisis_recibidos(self):
        turno = self.atencion.reservar_turno(TOBY, GOMEZ, "2026-10-05 09:00", "2026-10-05 09:30")
        consulta = self.atencion.registrar_consulta(
            TOBY, GOMEZ, "2026-10-05 09:05", "Consulta", 20000, "Decaimiento", "Anemia leve",
            "Suplemento de hierro por 30 días", turno, [(ANTIRRABICA_PERRO, "L-2026-7")],
        )["consulta_id"]
        inicio = datetime(2026, 10, 5, 9, 15)
        muestras = self._derivar(consulta, [HEMOGRAMA, BIOQUIMICO], REF_01, [TRANSPORTE_EJEMPLO], "Intacto",
                                 inicio, horas_de_viaje=3)
        self._analizar(muestras, datetime(2026, 10, 6, 9, 0), ["Hto 32%", "Glucosa 92 mg/dL"])
        self.laboratorio.emitir_comprobante(consulta, "2026-10-06 18:00")

    def _control_con_vacunas(self):
        consulta = self.atencion.registrar_consulta(
            MORA, FERREYRA, "2026-10-08 11:00", "Control", 15000, "Vacunación", "Sana", None,
            vacunas=[(ANTIRRABICA_GATO, "L-2026-8"), (TRIPLE_FELINA, "L-2026-9")],
        )["consulta_id"]
        self.laboratorio.emitir_comprobante(consulta, "2026-10-08 11:30")

    def _urgencia_con_precinto_roto(self):
        consulta = self.atencion.registrar_consulta(
            LUNA, RIOS, "2026-10-12 22:00", "Urgencia", 30000, "Vómitos", "Infección urinaria",
            "Antibiótico por 7 días",
        )["consulta_id"]
        self._derivar(consulta, [URIANALISIS], REF_02, [LOGISTICA_FICTICIA], "Roto",
                      datetime(2026, 10, 12, 22, 15), horas_de_viaje=5)
        self.laboratorio.emitir_comprobante(consulta, "2026-10-13 10:00")

    def _biopsia_recibida(self):
        consulta = self.atencion.registrar_consulta(
            SIMON, RIOS, "2026-10-15 10:00", "Consulta", 22000, "Nódulo en el lomo", "Nódulo a estudiar",
            "Control en 15 días",
        )["consulta_id"]
        muestras = self._derivar(consulta, [HISTOPATOLOGIA], AMB_01, [LOGISTICA_FICTICIA], "Intacto",
                                 datetime(2026, 10, 15, 10, 15), horas_de_viaje=6)
        self._analizar(muestras, datetime(2026, 10, 19, 15, 0), ["Lipoma benigno"])
        self.laboratorio.emitir_comprobante(consulta, "2026-10-19 18:00")

    def _urgencia_con_traspaso_y_precinto_roto(self):
        consulta = self.atencion.registrar_consulta(
            TOBY, FERREYRA, "2026-10-20 08:00", "Urgencia", 30000, "Diarrea", "Gastroenteritis",
            "Dieta blanda y probióticos",
        )["consulta_id"]
        self._derivar(consulta, [COPROPARASITOLOGICO, HEMOGRAMA], REF_01, [TRANSPORTE_EJEMPLO, LOGISTICA_FICTICIA],
                      "Roto", datetime(2026, 10, 20, 8, 15), horas_de_viaje=4)
        self.laboratorio.emitir_comprobante(consulta, "2026-10-20 18:00")

    def _consulta_con_analisis_por_informar(self):
        """Queda recibido sin resultado, para probar la carga desde la pantalla de Laboratorio."""
        consulta = self.atencion.registrar_consulta(
            MORA, GOMEZ, "2026-10-28 16:00", "Consulta", 20000, "Pérdida de peso", "A estudiar",
            "Dieta de recuperación",
        )["consulta_id"]
        self._derivar(consulta, [BIOQUIMICO], REF_02, [TRANSPORTE_EJEMPLO], "Intacto",
                      datetime(2026, 10, 28, 16, 15), horas_de_viaje=2)

    def _derivar(self, consulta, tipos, conservadora, transportistas, precinto, inicio, horas_de_viaje):
        """Lleva las muestras desde la extracción hasta la recepción y devuelve sus ids."""
        codigos = self.atencion.emitir_orden(
            consulta, LABORATORIO, _texto(inicio + timedelta(minutes=5)),
            [(tipo, _texto(inicio)) for tipo in tipos], RESPONSABLE,
        )["codigos"]
        muestras = [m["id"] for m in self.envios.listar_muestras_para_empaquetar() if m["codigo"] in codigos]
        remito = self.envios.empaquetar(muestras, conservadora, _texto(inicio + timedelta(minutes=30)),
                                        RESPONSABLE)["remito_id"]
        despacho = inicio + timedelta(hours=1)
        self.envios.registrar_evento(remito, transportistas[0], "Despacho", _texto(despacho), "Clínica de origen", 5,
                                     "Chofer de salida")
        for transportista in transportistas[1:]:
            self.envios.registrar_evento(remito, transportista, "Traspaso", _texto(despacho + timedelta(hours=1)),
                                         "Depósito intermedio", 6, "Chofer de relevo")
        arribo = despacho + timedelta(hours=horas_de_viaje)
        self.envios.registrar_evento(remito, transportistas[-1], "Arribo", _texto(arribo), "Laboratorio Central", 6,
                                     "Chofer de llegada")
        observacion = "Precinto cortado" if precinto == "Roto" else None
        self.envios.registrar_recepcion(remito, precinto, _texto(arribo), BIOQUIMICA, 6, observacion)
        return muestras

    def _analizar(self, muestras, fecha, valores):
        for muestra, valor in zip(muestras, valores):
            self.laboratorio.registrar_resultado(muestra, _texto(fecha), BIOQUIMICA, valor, "Informado")
