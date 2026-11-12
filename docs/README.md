# Documentación del proyecto

Sistema de veterinaria: red de clínicas y derivación de laboratorio. Trabajo práctico integrador de Desarrollo de Aplicaciones con Objetos (UTN FRC), Tema 2, grupo 81.

Si sos un agente o alguien nuevo en el proyecto, leé estos archivos antes de cambiar código:

| Archivo | Para qué sirve |
| --- | --- |
| [alcance.md](alcance.md) | Qué pide la consigna y qué queda afuera |
| [estado.md](estado.md) | Qué está hecho, qué se probó y qué falta |
| [decisiones.md](decisiones.md) | Decisiones tomadas y sus motivos |
| [arquitectura.md](arquitectura.md) | Capas, patrones y dónde va cada cosa |
| [diagramas/diagramas.html](diagramas/diagramas.html) | DER, diagrama de clases general, capas y uno por patrón (State, DAO, Factory Method). Se abre con doble clic en el navegador. Las mismas imágenes están en `diagramas/` como `.png` y `.svg` |

## Reglas para trabajar en el proyecto

1. **Sin sobreingeniería.** Es un proyecto escolar. Usar solo temas y librerías vistos en la materia (lista en [arquitectura.md](arquitectura.md)). Si hace falta algo más, preguntar antes.
2. **Respetar las capas.** La interfaz no contiene SQL ni reglas de negocio, y el SQL vive solo en `dao/` y `datos/`.
3. **No tocar lo inmutable.** Los historiales de estado solo admiten `INSERT`. Los cambios de estado de muestras y remitos pasan siempre por el patrón State.
4. **Agregar tests.** Toda regla nueva lleva su test, y la suite completa debe pasar antes de dar algo por terminado.
5. **Escribir en español.** El código, los mensajes y la documentación siguen el vocabulario del dominio.
6. **Mantener estos documentos al día.** Si cambia el estado o se toma una decisión, actualizar `estado.md` o `decisiones.md` en el mismo cambio.
7. **No inventar reglas en silencio.** Si la consigna no define algo, proponer una opción, y registrarla en `decisiones.md` una vez confirmada.

## Documentos de origen

Están fuera de esta carpeta, en la carpeta de la materia, y mandan sobre esta documentación:

- `entrega1-tp-dao/tema2.pdf`: consigna.
- `entrega1-tp-dao/Presentacion-grupo81-Tema2.pdf`: alcance presentado por el grupo.
- `entrega1-tp-dao/DER-Tema2-SQLite.png`: modelo de datos.
- `filminas_DAO/`: material de la materia, que define el nivel esperado.

## Comandos

Con el entorno virtual activado (ver el [README principal](../README.md)) y desde la raíz del proyecto:

```powershell
python main.py          # abre la aplicación
python cargar_demo.py   # carga atenciones ficticias para probar
pytest                  # ejecuta todos los tests
```
