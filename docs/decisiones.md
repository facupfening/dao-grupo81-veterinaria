# Decisiones tomadas

Registra lo que la consigna, la presentación o el DER no definían. Antes de cambiar una decisión, considerá su motivo y actualizá este archivo.

## Tecnología

| Decisión | Motivo |
| --- | --- |
| Flet para la interfaz | La guía de la materia ya muestra la separación en capas |
| `sqlite3` directo con DAO, sin SQLAlchemy | El diseño depende de triggers y `CHECK` propios de SQLite |
| Versiones fijas en `requirements.txt` | Flet cambia rápido y su API varía entre versiones |
| Entorno virtual en `.venv`, dentro del proyecto | Es lo que indica la guía de Flet de la materia. No se comparte: cada integrante crea el suyo |

## Patrones

| Decisión | Motivo |
| --- | --- |
| State para muestra y remito | Lo exige la presentación del grupo |
| DAO como segundo patrón | Ya se usa para el acceso a datos y la materia lo presenta como patrón. Si la cátedra no lo acepta, la alternativa simple es Singleton para la conexión |

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
| Los gráficos solo aparecen en el PDF | Es lo que muestra la materia con ReportLab y Matplotlib, y mantiene simple la pantalla |

## Clases del dominio

Solo `Cliente`, `Mascota`, `Muestra` y `Remito` son clases. Las demás entidades se manejan como filas de la base, igual que el ejemplo `PersonaDAO` de las filminas. Es lo más simple, pero sigue abierto si conviene crear más clases: ver [estado.md](estado.md).
