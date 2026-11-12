# Decisiones tomadas

Registra lo que la consigna, la presentación o el DER no definían. Antes de cambiar una decisión, considerá su motivo y actualizá este archivo.

## Tecnología

| Decisión | Motivo |
| --- | --- |
| Flet para la interfaz | La guía de la materia ya muestra la separación en capas |
| `sqlite3` directo con DAO, sin SQLAlchemy | El diseño depende de triggers y `CHECK` propios de SQLite |
| `openpyxl` para exportar a Excel | Se pidió exportar a Excel y la librería estándar no escribe `.xlsx`. Es la única librería que se agregó fuera de las vistas en la materia |
| Versiones fijas en `requirements.txt` | Flet cambia rápido y su API varía entre versiones |
| Entorno virtual en `.venv`, dentro del proyecto | Es lo que indica la guía de Flet de la materia. No se comparte: cada integrante crea el suyo |

## Patrones

| Decisión | Motivo |
| --- | --- |
| State para muestra y remito | Lo exige la presentación del grupo |
| DAO como segundo patrón | Ya se usa para el acceso a datos y la materia lo presenta como patrón. Si la cátedra no lo acepta, queda Factory Method |
| Factory Method para exportar reportes | Hay tres formatos (PDF, Excel, Markdown) que siguen los mismos pasos y solo difieren en el documento que se crea. Es la versión del libro de patrones: un método fábrica abstracto (`crear_documento`) que cada subclase redefine. Agregar un formato no cambia el gestor ni la pantalla |

## Trazabilidad y envíos

| Decisión | Motivo |
| --- | --- |
| Las muestras pasan a En tránsito junto con el remito, en el primer traspaso o arribo posterior al despacho | Mantiene alineados los estados. Mientras el remito está Despachado, siguen Empaquetadas |
| La recepción exige un remito En tránsito | Un envío directo registra Despacho y Arribo antes de recibir |
| Los traspasos siguientes no agregan filas al historial | El estado no cambia; quedan como eventos de envío |
| No se puede despachar un remito vacío | Un remito agrupa muestras |
| El historial no acepta fechas anteriores a su último registro | Evita tiempos negativos en los reportes |
| Antes de cambiar el remito se verifican todas sus muestras | Evita cambios a medias |
| La temperatura fuera de rango se registra, pero no rechaza | La presentación solo rechaza por precinto roto |

## Empaquetado

| Decisión | Motivo |
| --- | --- |
| El rango de la conservadora debe quedar dentro del que tolera la muestra | Garantiza una temperatura válida durante todo el viaje |
| La conservadora queda En uso hasta la recepción, aceptada o rechazada | Una conservadora no puede viajar en dos remitos a la vez |
| Todas las muestras de un remito tienen la misma clínica y el mismo laboratorio | El remito tiene un solo origen y un solo destino |

## Atención y agenda

| Decisión | Motivo |
| --- | --- |
| Los turnos cancelados liberan el horario y no se reactivan si ese horario se ocupó | Un turno cancelado no ocupa la agenda |
| La clínica de la consulta se toma del veterinario que atendió | Refleja quién atendió realmente |
| El turno de una consulta debe ser de esa mascota y estar Reservado | Evita atender un turno ajeno o repetido |
| La próxima dosis se calcula como fecha de aplicación más intervalo de la vacuna | El catálogo define el intervalo |

## Bajas y datos

| Decisión | Motivo |
| --- | --- |
| No se borra un cliente con mascotas ni una mascota con turnos o consultas | Se conserva la trazabilidad |
| Códigos de muestras, remitos, precintos y comprobantes generados automáticamente (`M-000001`) | Garantiza que sean únicos. El precinto podría venir impreso; se puede cambiar si se pide |
| Los datos de ejemplo no incluyen atenciones | Se generan con los procesos, para que los historiales queden completos. Para eso está `cargar_demo.py` |
| La demostración carga 25 consultas que cubren todas las opciones | Así cada reporte, filtro y estado se puede mostrar sin cargar datos a mano. Los clientes y mascotas nuevos también se dan de alta con los gestores |
| La demostración deja muestras a mitad de camino (Extraídas, Empaquetadas, En tránsito y Recibidas) | Para poder empaquetar, despachar, recibir y cargar resultados en vivo desde la interfaz. La conservadora REF-01 queda Disponible para empaquetar |
| Se agregaron clínicas, veterinarios, un laboratorio y un transportista a los datos de ejemplo: 5 clínicas, cada una con al menos un veterinario | Se pidió una red de 5 clínicas. Cada clínica necesita un veterinario porque la consulta toma la clínica del veterinario; la demostración tiene atenciones en las 5 |
| Un detalle de comprobante corresponde a una consulta o a una muestra, nunca a ambas | Permite desglosar la facturación por servicio |

## Facturación

| Decisión | Motivo |
| --- | --- |
| El comprobante se emite por consulta | Es la unidad de atención |
| Un análisis que termina después va en otro comprobante, sin repetir líneas | Permite facturar sin esperar todos los resultados |
| Las muestras rechazadas nunca se facturan | Lo exige la presentación |

## Reportes

| Decisión | Motivo |
| --- | --- |
| Un rechazo se atribuye al transportista del último evento | Es quien entregó el remito. Si hubo un traspaso, el anterior no figura aunque el precinto se haya roto en su tramo |
| El tiempo de tránsito incluye remitos rechazados | También viajaron |
| El tiempo de procesamiento solo cuenta muestras analizadas | Las demás no tienen resultado |
| Los promedios generales ponderan por cantidad | El promedio de promedios daría un valor incorrecto |
| Las vacunas se evalúan al último día del período, o a la fecha actual si no se indica | Da una foto coherente con el período pedido |
| Los gráficos solo aparecen en el archivo exportado, no en pantalla | Es lo que muestra la materia con ReportLab y Matplotlib, y mantiene simple la pantalla |
| Los tres formatos llevan las mismas tablas y gráficos | El reporte se arma una sola vez (`Reporte`) y cada exportador solo cambia cómo se escribe |
| En Excel, las tablas van en la hoja "Datos" y los gráficos en la hoja "Gráficos" | Las imágenes no tapan los datos, sin calcular cuántas filas ocupa cada tabla |
| En Markdown, cada gráfico se guarda como PNG al lado del `.md`, que lo enlaza | Markdown es texto y no puede llevar la imagen adentro |

## Interfaz

| Decisión | Motivo |
| --- | --- |
| Las altas se cargan en una ventana emergente (`Dialogo`) que abre un botón "Nuevo …" | La pantalla queda despejada para el listado, y el formulario aparece solo cuando hace falta |
| Editar abre la misma ventana que el alta, con los datos cargados | Un solo formulario por entidad |
| Con una ventana abierta, el error se muestra dentro de ella | El usuario lo ve sin cerrar la ventana ni perder lo cargado |
| Después de cada acción, `_intentar()` llama a `page.update()` | Flet solo redibuja la ventana donde se hizo clic; sin esto, la tabla de atrás no mostraba el registro nuevo |
| Los campos obligatorios llevan `*` en la etiqueta, y cada ventana muestra la leyenda "* Obligatorio" | El usuario sabe qué puede dejar vacío. Coincide con lo que exige el negocio |
| Los colores están en constantes al principio de `interfaz/pantalla.py` | Cambiar el color de toda la aplicación es tocar una línea |
| La sección "Turnos y veterinarios" muestra una tarjeta por veterinario (nombre, matrícula y clínica) con todos sus turnos, y el veterinario se elige dentro de la ventana "Registrar turno" | Se pidió ver la agenda de todos sin filtrar primero. Reemplaza al desplegable de veterinario que estaba arriba de la tabla |
| Debajo de los veterinarios, la misma sección lista las clínicas (nombre, dirección, teléfono y cantidad de veterinarios) | Se pidió verlas en la pestaña. La cantidad se cuenta con la lista de veterinarios que la pantalla ya trajo, sin otra consulta |
| Las fechas no se escriben: se eligen con un calendario (`DatePicker`) y la hora con un reloj (`TimePicker`), con `campo_fecha()` | Evita errores de formato. El campo guarda el mismo texto `AAAA-MM-DD HH:MM`, así el negocio no cambia |
| La fecha y la hora tienen un botón cada una, en lugar de abrir el reloj al cerrar el calendario | Flet no abre el segundo selector mientras el primero se está cerrando |
| Calendario y reloj en español (`es-AR`, 24 horas) | Es el idioma de la aplicación |
| `campo_fecha(..., desde=otro_campo)` deshabilita en el calendario los días anteriores a ese campo. Se usa en Hasta (Reportes) y en Fin (Turnos) | Evita elegir un período al revés. El negocio lo sigue rechazando por si Desde se cambia después |
| La hora de Fin no se limita en el reloj | El reloj de Flet no tiene hora mínima; si Fin queda antes de Inicio el mismo día, el negocio lo rechaza |
| Los campos numéricos usan `input_filter` de Flet: DNI solo dígitos (máximo 8), teléfono dígitos, espacios, `+` y `-`, precio y peso decimales con coma o punto, temperaturas decimales con signo menos | Evita tipear letras. La validación al guardar se mantiene como segunda barrera |
| Cada botón "Nuevo …" vacía su formulario con `vaciar()` antes de abrir la ventana | Evita que aparezcan datos de una carga anterior. En los desplegables también se borra `text`, porque Flet sigue mostrando la opción anterior aunque el valor sea `None` |
| Las vacunas y muestras agregadas se muestran como lista (`item_de_lista()`), cada una con un botón para quitarla | Se ve qué se va a registrar y se puede corregir antes de guardar |
| `Dialogo.abrir()` no hace nada si la ventana ya está abierta | Un doble clic hacía que Flet lanzara `RuntimeError: Dialog is already opened` |
| Sección propia "Muestras" con `GestorMuestras`, que solo consulta | La trazabilidad atraviesa varios procesos (atención, envíos, laboratorio); un gestor aparte evita repartirla. No cambia estados: eso sigue en los gestores de cada proceso |
| Cada estado tiene un color fijo (`COLORES_ESTADO`) y se muestra con `etiqueta_estado()` en todas las pantallas | Se reconoce la etapa de un vistazo. Los estados de remito usan el color del estado de muestra equivalente |
| La trazabilidad (Muestras, Envíos), la historia clínica y el detalle de comprobante se abren en un `PanelLateral` a la derecha, que se cierra con la X | Se ve el detalle sin perder el listado. Flet lo permite con una fila de dos columnas, así que no hizo falta una ventana emergente |
| En Muestras, Envíos y comprobantes, tocar la fila también abre el detalle | En pantallas angostas la columna de acciones queda fuera de la vista |
| Los datos de ejemplo traen 11 conservadoras: REF-01 a REF-06 (2 a 8 °C), AMB-01 a AMB-03 (15 a 25 °C) y CON-01 a CON-03 (-20 a -10 °C); REF-03 está fuera de servicio | Hay varias disponibles de cada rango para probar empaquetados seguidos. Las nuevas van al final, así las de siempre conservan su id |
| La tabla de Consultas tiene una columna Clínica | Se pidió ver dónde se atendió cada consulta. Sale de `consultas.clinica_id`, sin cambiar el esquema |
| En Consultas, las muestras se muestran en grilla de hasta 3 por renglón y la fila crece en alto | La fila no se estira a lo ancho cuando una consulta tiene muchas muestras |
| El recorrido de una muestra indica el próximo paso y en qué pantalla se hace | Responde "¿dónde está y qué falta?" sin tener que conocer el flujo |
| Laboratorio muestra las muestras pendientes de resultado y todos los comprobantes, no solo el último | Se puede volver a consultar cualquier comprobante. La búsqueda es por número o por nombre del cliente, igual que la de clientes |

## Clases del dominio

Solo `Cliente`, `Mascota`, `Muestra` y `Remito` son clases. Las demás entidades se manejan como filas de la base, igual que el ejemplo `PersonaDAO` de las filminas. Es lo más simple, pero sigue abierto si conviene crear más clases: ver [estado.md](estado.md).
