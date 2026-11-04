# Estado del proyecto

Última actualización: 2026-11-04. Al modificar el proyecto, actualizar este archivo.

## Hecho

| Parte | Estado |
| --- | --- |
| Base de datos | 25 tablas del DER, `CHECK` y 6 triggers |
| Datos de ejemplo | Catálogos, clínicas, clientes y mascotas, cargados automáticamente |
| Patrón State | Muestra y remito, con historial y paso de estado en conjunto |
| DAO | Una clase por entidad principal |
| Procesos 1 a 7 | Implementados en `negocio/` |
| Interfaz de Flet | 8 secciones: Clientes, Mascotas, Turnos, Consultas, Empaquetado, Envíos, Laboratorio y Reportes |
| Reportes | Los 5 prometidos, en pantalla y en PDF con gráficos |
| Datos de demostración | `cargar_demo.py`, a pedido |
| Tests | 244 con pytest, todos pasan en un entorno limpio instalado desde `requirements.txt` (Python 3.11 y 3.14) |

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

- Empaquetado, Envíos y Laboratorio con clics reales; solo se probaron por código.
- El diseño del PDF de Facturación (su contenido sí se revisó).
- El ajuste de los ejes enteros en los gráficos, hecho después de revisar los PDF.

## Falta

- **Git:** el repositorio y el `.gitignore` ya existen, pero todavía no hay ningún commit.
- **Modelo de clases:** turnos, consultas, órdenes y comprobantes siguen siendo filas de la base. Falta decidir si crear esas clases, porque la consigna evalúa el modelo.
- **Segundo patrón:** confirmar con la cátedra que DAO se acepte.

## Limitaciones conocidas

- Dar de baja actúa sin pedir confirmación, aunque el negocio impide borrar clientes con mascotas y mascotas con atenciones.
- Las fechas se escriben a mano como `AAAA-MM-DD HH:MM`, sin calendario.
- Clínicas, veterinarios, laboratorios, análisis, vacunas, conservadoras y transportistas no tienen pantalla de edición.
- No se compara la fecha de extracción con la de la consulta. Dentro de cada historial sí se rechazan fechas hacia atrás.
- Algunos listados de los DAO no tienen test propio, aunque varios se usan en las pruebas de pantallas y reportes.
