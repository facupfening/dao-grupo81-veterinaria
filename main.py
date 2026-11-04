import flet as ft

from datos.base_datos import inicializar
from interfaz.aplicacion import iniciar


def main():
    inicializar()
    ft.run(iniciar)


if __name__ == "__main__":
    main()
