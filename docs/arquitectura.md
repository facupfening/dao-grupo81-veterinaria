# Arquitectura

## Capas

```text
interfaz/  → negocio/  → dao/  → SQLite
              ↓
          modelos/ + estados/
```

| Carpeta | Responsabilidad | Regla |
| --- | --- | --- |
| `interfaz/` | Pantallas de Flet | Sin SQL ni reglas de negocio; un test lo controla |
| `negocio/` | Gestores con las reglas de cada proceso | Cada operación es una transacción |
| `dao/` | SQL de cada entidad | Recibe la conexión; no confirma ni deshace cambios |
| `modelos/` | Clases del dominio y validaciones | No acceden a la base |
| `estados/` | Estados de muestra y remito | Definen qué transiciones son válidas |
| `datos/` | Conexión, esquema y datos de ejemplo | `PRAGMA foreign_keys` se activa en cada conexión |
| `reportes/` | Contenido del reporte y generación del PDF | No conoce la base |
| `tests/` | Pruebas con pytest | Usan bases temporales, nunca `veterinaria.db` |

## Dónde agregar cada cosa

- **Una regla de negocio:** en el gestor de `negocio/` que corresponda, con su test.
- **Una consulta SQL:** en el DAO de `dao/`, y se expone por un método del gestor.
- **Una transición de estado:** en `estados/`, redefiniendo el método en el estado que la admite. Por defecto, la clase base la rechaza.
- **Una pantalla:** una subclase de `Pantalla` en `interfaz/`, registrada en `aplicacion.py`. Si crea algo, su formulario va en un `Dialogo`, abierto con un botón de `boton_nuevo()`.
- **Un reporte:** una consulta en `ReporteDAO`, un método en `GestorReportes` y su entrada en `NOMBRES_REPORTES`.

## Flujo de una operación

1. La pantalla toma los valores y llama a un gestor.
2. El gestor abre una transacción con `_transaccion()`, que usa una conexión propia para esa operación.
3. El gestor valida, usa los DAO y los modelos, y devuelve el resultado.
4. Ante un error se deshace todo y se dispara `ErrorNegocio`, con un mensaje apto para el usuario. La pantalla lo muestra en rojo.

La conexión no se comparte entre operaciones porque Flet puede ejecutar los eventos en distintos hilos, y una conexión de `sqlite3` no puede pasar de un hilo a otro.

## Patrones

- **State:** `Muestra` y `Remito` heredan de `Trazable`, que guarda el estado y el historial, y delegan las operaciones en su estado actual. Un estado concreto decide la transición. `Remito` arrastra a sus muestras.
- **DAO:** una clase por entidad principal, que hereda de `BaseDAO`.

## Persistir un cambio de estado

Los objetos cambian primero en memoria. Después, `guardar_estado()` actualiza `estado_actual` e inserta solo los registros nuevos del historial, comparando con los ya guardados. Los triggers rechazan cualquier `UPDATE` o `DELETE` sobre los historiales.

## Convenciones

- Fechas en texto: `AAAA-MM-DD HH:MM`, para poder compararlas directamente. `modelos/validaciones.py` exige ese formato exacto.
- Booleanos como `INTEGER` 0/1, y estados como `TEXT` restringidos con `CHECK`.
- Los nombres de los estados deben coincidir con los `CHECK` del esquema; un test lo controla.

## Librerías permitidas

Vistas en la materia y ya usadas: `sqlite3`, `abc`, `flet`, `reportlab`, `matplotlib` y `pytest`. También están en las filminas, sin usar: `sqlalchemy`, `tkinter` y `csv`. Para cualquier otra, preguntar antes.

## Probar la interfaz sin abrir la ventana

- **Eventos:** `tests/test_interfaz.py` carga valores en los controles y llama a los mismos métodos que los botones.
- **En un navegador:** definir la variable `FLET_FORCE_WEB_SERVER=true` y usar `ft.run(main, view=None, port=8601)` con una base temporal. Si el navegador queda oculto o en segundo plano, la página se reconecta y parece no responder: no es una falla de la aplicación.
- **API de Flet:** es la versión 1.0, distinta de ejemplos más viejos. Por ejemplo, `Dropdown` usa `on_select`, y se usa `ft.Button` y `ft.run`.
