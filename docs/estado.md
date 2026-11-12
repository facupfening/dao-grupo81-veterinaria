# Estado del proyecto

Última actualización: 2026-11-12. Al modificar el proyecto, actualizar este archivo.

## Hecho

| Parte | Estado |
| --- | --- |
| Base de datos | 25 tablas del DER, `CHECK` y 6 triggers |
| Datos de ejemplo | Catálogos (5 clínicas, 6 veterinarios, 2 laboratorios, 3 transportistas), 3 clientes y 4 mascotas, cargados automáticamente |
| Patrón State | Muestra y remito, con historial y paso de estado en conjunto |
| DAO | Una clase por entidad principal |
| Procesos 1 a 7 | Implementados en `negocio/` |
| Interfaz de Flet | 9 secciones: Clientes, Mascotas, Turnos, Consultas, Empaquetado, Envíos, Laboratorio, Muestras y Reportes. Colores en verde azulado, listados en tarjetas y altas en ventanas emergentes que se abren con botones "Nuevo …". Las fechas se eligen con calendario y las horas con reloj. La tabla de Consultas muestra la clínica de cada atención. DNI, teléfono, precio, peso y temperaturas no dejan tipear letras. Los campos obligatorios llevan `*`. El calendario de Hasta (Reportes) y de Fin (Turnos) no ofrece días anteriores a Desde e Inicio. Laboratorio lista las muestras pendientes y todos los comprobantes, con búsqueda por número o cliente y su detalle. Cada ventana se abre vacía; las vacunas y muestras agregadas se ven en lista y se pueden quitar |
| Trazabilidad de muestras | Sección Muestras: cantidad por estado, filtro, búsqueda y recorrido completo de cada muestra con su próximo paso. El estado se ve en color también en Consultas (grilla de hasta 3 por renglón), Envíos y la historia clínica. La trazabilidad, la historia clínica y el detalle de comprobante se abren en un panel a la derecha del listado, tocando el ícono o la fila |
| Reportes | Los 5 prometidos, en pantalla y exportados a PDF, Excel o Markdown con sus tablas y gráficos |
| Patrón Factory Method | Exportación de reportes: un exportador y un documento por formato |
| Datos de demostración | `cargar_demo.py`, a pedido: 25 consultas, 10 clientes y 13 mascotas. Cubren todos los estados de muestras, remitos, turnos y conservadoras, los 3 tipos de consulta, los 6 análisis, las 5 clínicas, prioridad Normal y Urgente, precintos intactos y rotos, y vacunas al día, vencidas y faltantes. Un test controla que no falte ninguna opción |
| Diagramas | En `docs/diagramas/`: DER (controlado contra la base: tablas, columnas y claves foráneas), clases general, capas, State (clases y transiciones de muestra y remito), DAO, Factory Method y las máquinas de estado UML de muestra y remito (con evento, condición y acción en cada transición). Cada uno en `diagramas.html` y como `.png` y `.svg` |
| Comentarios en el código | Breves, en los puntos menos obvios: SQL de reportes, pasos del empaquetado, State y conversión de errores |
| Tests | 285 con pytest, todos pasan en un entorno limpio instalado desde `requirements.txt` (Python 3.11 y 3.14) |

## Cómo se verificó

- **Tests:** base de datos, transiciones, procesos, cálculos de reportes y eventos de las pantallas sin abrir la ventana.
- **Clics reales en navegador:**
  - Clientes: alta y error por DNI repetido.
  - Consultas: elegir mascota y registrar una consulta.
  - Reportes: error por no elegir, vista de Facturación y exportación a PDF.
  - Reportes: exportación de Facturación a Excel y a Markdown; se revisó que ambos archivos tengan las tablas y el gráfico.
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
- El aspecto del Excel abierto en Excel o LibreOffice (su contenido se revisó por código).

## Falta

- **Modelo de clases:** turnos, consultas, órdenes y comprobantes siguen siendo filas de la base. Falta decidir si crear esas clases, porque la consigna evalúa el modelo.
- **Patrones:** State y Factory Method son del libro de patrones; DAO queda como tercero aunque la cátedra no lo cuente.

## Limitaciones conocidas

- Dar de baja actúa sin pedir confirmación, aunque el negocio impide borrar clientes con mascotas y mascotas con atenciones.
- Clínicas, veterinarios, laboratorios, análisis, vacunas, conservadoras y transportistas no tienen pantalla de edición.
- No se compara la fecha de extracción con la de la consulta. Dentro de cada historial sí se rechazan fechas hacia atrás.
- Algunos listados de los DAO no tienen test propio, aunque varios se usan en las pruebas de pantallas y reportes.
