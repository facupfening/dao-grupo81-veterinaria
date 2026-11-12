import flet as ft

from datos.base_datos import inicializar
from interfaz.aplicacion import iniciar


def main():
    inicializar()  # crea la base y carga los datos de ejemplo si todavía no existen
    ft.run(iniciar)  # abre la ventana de Flet


if __name__ == "__main__":
    main()
