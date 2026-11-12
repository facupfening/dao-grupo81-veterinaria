# Veterinaria: Red de Clínicas y Derivación de Laboratorio

Trabajo práctico integrador de Desarrollo de Aplicaciones con Objetos (UTN FRC), Tema 2, grupo 81.

El alcance, el estado, las decisiones y la arquitectura están en [docs/](docs/README.md).

## Levantar el proyecto después de descargarlo

Requiere Python 3.11 o superior; las dependencias y los tests se verificaron con Python 3.11 y 3.14. Los comandos son para Windows y se ejecutan una sola vez, salvo los de los pasos 3 y 5. Son iguales en Git Bash y en PowerShell, salvo la activación del paso 3, que cambia según la terminal.

**1. Entrar a la carpeta del proyecto**

Abrí la terminal en la carpeta donde está este archivo `README.md`.

**2. Crear el entorno virtual**

```bash
py -3.11 -m venv .venv
```

Si tenés Python 3.14, también podés usar `py -3.14 -m venv .venv`. Si `.venv` ya existe y fue creado con una versión anterior, eliminá esa carpeta antes de crear el entorno nuevo.

**3. Activar el entorno virtual**

Hay que hacerlo cada vez que abrís una terminal nueva. Usá el comando de tu terminal, porque el de la otra no funciona.

En **Git Bash**:

```bash
source .venv/Scripts/activate
```

En **PowerShell**:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell avisa que la ejecución de scripts está deshabilitada, ejecutá esto y volvé a activarlo. Solo afecta a esa terminal y no hace falta en Git Bash:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

**No sigas hasta ver `(.venv)` al inicio de la línea de la terminal.** Si no aparece, el paso siguiente instala todo en el Python global en lugar de en el proyecto.

Comprobá también que `python --version` indique Python 3.11 o superior. Activar un `.venv` creado con Python 3.6 no lo actualiza.

**4. Instalar las dependencias**

```bash
python -m pip install -r requirements.txt
```

**5. Abrir la aplicación**

```bash
python main.py
```

La primera vez tarda un poco más porque Flet se prepara, y se crea `veterinaria.db` con los datos de ejemplo.

## Comandos opcionales

Cargar 25 atenciones ficticias que recorren todas las opciones del sistema (estados, reportes, vacunas, rechazos). Conviene ejecutarlo antes de cargar datos propios, porque no hace nada si la base ya tiene consultas. Para empezar de cero, borrá `veterinaria.db` y volvé a ejecutarlo:

```bash
python cargar_demo.py
```

Ejecutar los tests:

```bash
pytest
```

Para empezar de cero, borrá `veterinaria.db`. Los reportes exportados (PDF, Excel o Markdown) se guardan en `reportes_generados/`.

## Estructura

| Carpeta | Contenido |
| --- | --- |
| `datos/` | Conexión, tablas y triggers, datos de ejemplo |
| `modelos/` | Clases del dominio |
| `estados/` | Patrón State de la muestra y del remito |
| `dao/` | Una clase DAO por tabla principal, con el SQL |
| `negocio/` | Validaciones y reglas de cada proceso |
| `interfaz/` | Pantallas de Flet, sin SQL ni reglas de negocio |
| `reportes/` | Exportación de reportes (patrón Factory Method) a PDF, Excel y Markdown, con gráficos de Matplotlib |
| `tests/` | Pruebas con pytest |
| `docs/` | Documentación del proyecto |
