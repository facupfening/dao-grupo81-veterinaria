# Estado del proyecto

Última actualización: 2026-11-11. Al modificar el proyecto, actualizar este archivo.

## Hecho

| Parte | Estado |
| --- | --- |
| Base de datos | 25 tablas del DER, `CHECK` y 6 triggers |
| Datos de ejemplo | Catálogos, clínicas, clientes y mascotas, cargados automáticamente |
| Patrón State | Muestra y remito, con historial y paso de estado en conjunto |
| DAO | Una clase por entidad principal |
| Procesos 1 a 7 | Implementados en `negocio/` |
| Interfaz de Flet | 9 secciones: Clientes, Mascotas, Turnos, Consultas, Empaquetado, Envíos, Laboratorio, Muestras y Reportes. Colores en verde azulado, listados en tarjetas y altas en ventanas emergentes que se abren con botones "Nuevo …". Las fechas se eligen con calendario y las horas con reloj. DNI, teléfono, precio, peso y temperaturas no dejan tipear letras. Los campos obligatorios llevan `*`. El calendario de Hasta (Reportes) y de Fin (Turnos) no ofrece días anteriores a Desde e Inicio. Laboratorio lista las muestras pendientes y todos los comprobantes, con búsqueda por número o cliente y su detalle. Cada ventana se abre vacía; las vacunas y muestras agregadas se ven en lista y se pueden quitar |
| Trazabilidad de muestras | Sección Muestras: cantidad por estado, filtro, búsqueda y recorrido completo de cada muestra con su próximo paso. El estado se ve en color también en Consultas (grilla de hasta 3 por renglón), Envíos y la historia clínica. La trazabilidad, la historia clínica y el detalle de comprobante se abren en un panel a la derecha del listado, tocando el ícono o la fila |
| Reportes | Los 5 prometidos, en pantalla y en PDF con gráficos |
| Datos de demostración | `cargar_demo.py`, a pedido |
| Diagramas | DER y diagramas de clases en `docs/diagramas/diagramas.html`, armados a partir del código |
| Tests | 260 con pytest, todos pasan en un entorno limpio instalado desde `requirements.txt` (Python 3.11 y 3.14) |

## Cómo se verificó

- **Tests:** base de datos, transiciones, procesos, cálculos de reportes y eventos de las pantallas sin abrir la ventana.
- **Clics reales en navegador:**
  - Clientes: alta y error por DNI repetido.
  - Consultas: elegir mascota y registrar una consulta.
  - Reportes: error por no elegir, vista de Facturación y exportación a PDF.
  - Las primeras 7 secciones cargan.
- **PDF revisados a ojo:** Atenciones, Rechazos, Tratamientos y Tiempos.
- **Ventana de escritorio:** abre y conecta sin errores, sin clics ni revisión visual.

## Sin verificar todavía

- Pantallazo gris tras registrar la recepción de un remito: apareció una vez y no se pudo reproducir siempre. Después de los cambios (formularios vacíos al abrir y protección contra doble clic) no volvió a aparecer en las pruebas, pero no hay certeza de la causa.
- La tabla se actualiza al guardar desde una ventana: probado con clics en Mascotas (alta solo con obligatorios y bajas). En las demás pantallas, por código.
- Los filtros de tipeo se probaron con clics en DNI y teléfono; precio, peso y temperaturas, solo por código.
- Los selectores de fecha y hora se probaron con clics en Reportes (Desde) y en Nuevo comprobante; en las demás pantallas, solo por código.
- Las ventanas emergentes con clics reales: se abrieron Nuevo cliente (con su error) y Nueva consulta, y se cerraron con Cancelar. Las demás se probaron por código.

- Empaquetado, Envíos y Laboratorio con clics reales; solo se probaron por código.
- El diseño del PDF de Facturación (su contenido sí se revisó).
- El ajuste de los ejes enteros en los gráficos, hecho después de revisar los PDF.

## Falta

- **Modelo de clases:** turnos, consultas, órdenes y comprobantes siguen siendo filas de la base. Falta decidir si crear esas clases, porque la consigna evalúa el modelo.
- **Segundo patrón:** confirmar con la cátedra que DAO se acepte.

## Limitaciones conocidas

- Dar de baja actúa sin pedir confirmación, aunque el negocio impide borrar clientes con mascotas y mascotas con atenciones.
- Clínicas, veterinarios, laboratorios, análisis, vacunas, conservadoras y transportistas no tienen pantalla de edición.
- No se compara la fecha de extracción con la de la consulta. Dentro de cada historial sí se rechazan fechas hacia atrás.
- Algunos listados de los DAO no tienen test propio, aunque varios se usan en las pruebas de pantallas y reportes.
