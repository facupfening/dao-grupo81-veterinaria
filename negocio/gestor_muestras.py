from dao.muestra_dao import MuestraDAO
from estados.estado_muestra import ESTADOS_MUESTRA
from negocio.gestor import Gestor


class GestorMuestras(Gestor):
    """Consulta el estado y el recorrido de las muestras en todo el sistema."""

    def listar(self, busqueda="", estado=None):
        with self._transaccion() as conexion:
            return MuestraDAO(conexion).listar_detallado((busqueda or "").strip(), estado or None)

    def contar_por_estado(self):
        """Cantidad de muestras en cada estado, en el orden del ciclo de vida (incluye los que están en cero)."""
        with self._transaccion() as conexion:
            cantidades = MuestraDAO(conexion).contar_por_estado()
        return {estado: cantidades.get(estado, 0) for estado in ESTADOS_MUESTRA}

    def estados_por_consulta(self):
        """Para cada consulta, la lista de sus muestras como (código, estado)."""
        with self._transaccion() as conexion:
            filas = MuestraDAO(conexion).listar_estados_por_consulta()
        resultado = {}
        for fila in filas:
            resultado.setdefault(fila["consulta_id"], []).append((fila["codigo"], fila["estado"]))
        return resultado

    def obtener_trazabilidad(self, id):
        """La muestra con su historial de estados (patrón State) y su resultado, si ya lo tiene."""
        with self._transaccion() as conexion:
            dao = MuestraDAO(conexion)
            muestra = self._exigir(dao.obtener_por_id(id), "La muestra no existe")
            return {"muestra": muestra, "resultado": dao.obtener_resultado(id)}
