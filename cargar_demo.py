from datos.base_datos import RUTA_DB, inicializar
from negocio.datos_demo import CargaDemo


def main():
    inicializar()
    if CargaDemo(RUTA_DB).cargar():
        print("Datos de demostración cargados.")
    else:
        print("La base ya tiene consultas: no se cargó nada. Para empezar de cero, borrá veterinaria.db.")


if __name__ == "__main__":
    main()
