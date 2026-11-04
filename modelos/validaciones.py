from datetime import datetime

FORMATO_FECHA = "%Y-%m-%d"
FORMATO_FECHA_HORA = "%Y-%m-%d %H:%M"


def validar_fecha(valor, campo):
    """Exige el formato AAAA-MM-DD, para que las fechas se puedan comparar como texto."""
    _validar_formato(valor, FORMATO_FECHA, campo, "AAAA-MM-DD")


def validar_fecha_hora(valor, campo):
    """Exige el formato AAAA-MM-DD HH:MM, para que las fechas se puedan comparar como texto."""
    _validar_formato(valor, FORMATO_FECHA_HORA, campo, "AAAA-MM-DD HH:MM")


def _validar_formato(valor, formato, campo, descripcion):
    try:
        datetime.strptime(valor, formato)
    except (TypeError, ValueError):
        raise ValueError(f"{campo}: debe tener el formato {descripcion}") from None
    # strptime acepta fechas sin ceros a la izquierda, que después no se ordenarían bien como texto.
    if len(valor) != len(descripcion):
        raise ValueError(f"{campo}: debe tener el formato {descripcion}")


def validar_obligatorio(valor, campo):
    if valor is None or not str(valor).strip():
        raise ValueError(f"{campo}: es obligatorio")
    return str(valor).strip()
