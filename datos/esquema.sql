-- Esquema de la base de datos: Veterinaria, Red de Clínicas y Derivación de Laboratorio.
-- Convenciones: fechas en TEXT con formato 'AAAA-MM-DD HH:MM', booleanos como INTEGER 0/1
-- y estados como TEXT restringidos con CHECK.

-- ---------------------------------------------------------------------------
-- Atención clínica
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS especies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dni TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    telefono TEXT,
    email TEXT,
    direccion TEXT
);

CREATE TABLE IF NOT EXISTS clinicas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    direccion TEXT,
    telefono TEXT
);

CREATE TABLE IF NOT EXISTS veterinarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clinica_id INTEGER NOT NULL REFERENCES clinicas (id),
    matricula TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS mascotas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL REFERENCES clientes (id),
    especie_id INTEGER NOT NULL REFERENCES especies (id),
    nombre TEXT NOT NULL,
    raza TEXT,
    sexo TEXT,
    fecha_nacimiento TEXT,
    peso_kg REAL
);

CREATE TABLE IF NOT EXISTS historias_clinicas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mascota_id INTEGER NOT NULL UNIQUE REFERENCES mascotas (id),
    fecha_apertura TEXT NOT NULL,
    antecedentes TEXT
);

CREATE TABLE IF NOT EXISTS vacunas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    especie_id INTEGER NOT NULL REFERENCES especies (id),
    nombre TEXT NOT NULL,
    obligatoria INTEGER NOT NULL DEFAULT 0 CHECK (obligatoria IN (0, 1)),
    intervalo_dias INTEGER
);

CREATE TABLE IF NOT EXISTS turnos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mascota_id INTEGER NOT NULL REFERENCES mascotas (id),
    veterinario_id INTEGER NOT NULL REFERENCES veterinarios (id),
    inicio TEXT NOT NULL,
    fin TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'Reservado'
        CHECK (estado IN ('Reservado', 'Atendido', 'Cancelado')),
    CHECK (inicio < fin)
);

CREATE TABLE IF NOT EXISTS consultas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    historia_id INTEGER NOT NULL REFERENCES historias_clinicas (id),
    veterinario_id INTEGER NOT NULL REFERENCES veterinarios (id),
    clinica_id INTEGER NOT NULL REFERENCES clinicas (id),
    turno_id INTEGER UNIQUE REFERENCES turnos (id),
    fecha_hora TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('Consulta', 'Control', 'Urgencia')),
    motivo TEXT,
    diagnostico TEXT,
    tratamiento TEXT,
    precio REAL NOT NULL CHECK (precio >= 0)
);

CREATE TABLE IF NOT EXISTS aplicaciones_vacuna (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consulta_id INTEGER NOT NULL REFERENCES consultas (id),
    vacuna_id INTEGER NOT NULL REFERENCES vacunas (id),
    lote TEXT,
    fecha_aplicacion TEXT NOT NULL,
    fecha_proxima TEXT
);

-- ---------------------------------------------------------------------------
-- Derivación y trazabilidad
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS laboratorios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    direccion TEXT
);

CREATE TABLE IF NOT EXISTS tipos_analisis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    tipo_muestra TEXT NOT NULL,
    temp_min REAL NOT NULL,
    temp_max REAL NOT NULL,
    precio REAL NOT NULL CHECK (precio >= 0),
    CHECK (temp_min <= temp_max)
);

CREATE TABLE IF NOT EXISTS ordenes_derivacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consulta_id INTEGER NOT NULL REFERENCES consultas (id),
    laboratorio_id INTEGER NOT NULL REFERENCES laboratorios (id),
    fecha_emision TEXT NOT NULL,
    prioridad TEXT NOT NULL DEFAULT 'Normal' CHECK (prioridad IN ('Normal', 'Urgente')),
    observaciones TEXT
);

CREATE TABLE IF NOT EXISTS conservadoras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    capacidad INTEGER NOT NULL CHECK (capacidad > 0),
    temp_min REAL NOT NULL,
    temp_max REAL NOT NULL,
    estado TEXT NOT NULL DEFAULT 'Disponible'
        CHECK (estado IN ('Disponible', 'En uso', 'Fuera de servicio')),
    CHECK (temp_min <= temp_max)
);

CREATE TABLE IF NOT EXISTS remitos_biologicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT NOT NULL UNIQUE,
    clinica_id INTEGER NOT NULL REFERENCES clinicas (id),
    laboratorio_id INTEGER NOT NULL REFERENCES laboratorios (id),
    conservadora_id INTEGER NOT NULL REFERENCES conservadoras (id),
    fecha_emision TEXT NOT NULL,
    estado_actual TEXT NOT NULL DEFAULT 'Emitido'
        CHECK (estado_actual IN ('Emitido', 'Despachado', 'En tránsito', 'Recibido', 'Rechazado'))
);

CREATE TABLE IF NOT EXISTS muestras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    orden_id INTEGER NOT NULL REFERENCES ordenes_derivacion (id),
    tipo_analisis_id INTEGER NOT NULL REFERENCES tipos_analisis (id),
    remito_id INTEGER REFERENCES remitos_biologicos (id),
    codigo TEXT NOT NULL UNIQUE,
    fecha_extraccion TEXT NOT NULL,
    estado_actual TEXT NOT NULL DEFAULT 'Extraída'
        CHECK (estado_actual IN ('Extraída', 'Empaquetada', 'En tránsito', 'Recibida', 'Analizada', 'Rechazada'))
);

CREATE TABLE IF NOT EXISTS historial_estados_muestra (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    muestra_id INTEGER NOT NULL REFERENCES muestras (id),
    estado TEXT NOT NULL
        CHECK (estado IN ('Extraída', 'Empaquetada', 'En tránsito', 'Recibida', 'Analizada', 'Rechazada')),
    fecha_hora TEXT NOT NULL,
    responsable TEXT NOT NULL,
    observacion TEXT
);

CREATE TABLE IF NOT EXISTS historial_estados_remito (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    remito_id INTEGER NOT NULL REFERENCES remitos_biologicos (id),
    estado TEXT NOT NULL
        CHECK (estado IN ('Emitido', 'Despachado', 'En tránsito', 'Recibido', 'Rechazado')),
    fecha_hora TEXT NOT NULL,
    responsable TEXT NOT NULL,
    observacion TEXT
);

CREATE TABLE IF NOT EXISTS precintos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    remito_id INTEGER NOT NULL UNIQUE REFERENCES remitos_biologicos (id),
    numero TEXT NOT NULL UNIQUE,
    fecha_colocacion TEXT NOT NULL,
    colocado_por TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transportistas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    cuit TEXT NOT NULL UNIQUE,
    telefono TEXT
);

CREATE TABLE IF NOT EXISTS eventos_envio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    remito_id INTEGER NOT NULL REFERENCES remitos_biologicos (id),
    transportista_id INTEGER NOT NULL REFERENCES transportistas (id),
    tipo TEXT NOT NULL CHECK (tipo IN ('Despacho', 'Traspaso', 'Arribo')),
    fecha_hora TEXT NOT NULL,
    ubicacion TEXT NOT NULL,
    temperatura REAL NOT NULL,
    responsable TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS recepciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    remito_id INTEGER NOT NULL UNIQUE REFERENCES remitos_biologicos (id),
    fecha_hora TEXT NOT NULL,
    recibido_por TEXT NOT NULL,
    estado_precinto TEXT NOT NULL CHECK (estado_precinto IN ('Intacto', 'Roto')),
    temp_llegada REAL NOT NULL,
    observaciones TEXT
);

CREATE TABLE IF NOT EXISTS resultados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    muestra_id INTEGER NOT NULL UNIQUE REFERENCES muestras (id),
    fecha_hora TEXT NOT NULL,
    profesional TEXT NOT NULL,
    valores TEXT,
    conclusion TEXT
);

-- ---------------------------------------------------------------------------
-- Facturación
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS comprobantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT NOT NULL UNIQUE,
    cliente_id INTEGER NOT NULL REFERENCES clientes (id),
    clinica_id INTEGER NOT NULL REFERENCES clinicas (id),
    fecha TEXT NOT NULL,
    total REAL NOT NULL CHECK (total >= 0)
);

-- Cada detalle corresponde a una consulta o a una muestra, nunca a ambas ni a ninguna.
CREATE TABLE IF NOT EXISTS detalles_comprobante (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    comprobante_id INTEGER NOT NULL REFERENCES comprobantes (id),
    consulta_id INTEGER REFERENCES consultas (id),
    muestra_id INTEGER REFERENCES muestras (id),
    descripcion TEXT NOT NULL,
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario REAL NOT NULL CHECK (precio_unitario >= 0),
    CHECK ((consulta_id IS NULL) <> (muestra_id IS NULL))
);

-- ---------------------------------------------------------------------------
-- Triggers: historiales de estado inmutables (solo admiten INSERT)
-- ---------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS historial_muestra_no_update
BEFORE UPDATE ON historial_estados_muestra
BEGIN
    SELECT RAISE(ABORT, 'El historial de estados de la muestra no se puede modificar');
END;

CREATE TRIGGER IF NOT EXISTS historial_muestra_no_delete
BEFORE DELETE ON historial_estados_muestra
BEGIN
    SELECT RAISE(ABORT, 'El historial de estados de la muestra no se puede borrar');
END;

CREATE TRIGGER IF NOT EXISTS historial_remito_no_update
BEFORE UPDATE ON historial_estados_remito
BEGIN
    SELECT RAISE(ABORT, 'El historial de estados del remito no se puede modificar');
END;

CREATE TRIGGER IF NOT EXISTS historial_remito_no_delete
BEFORE DELETE ON historial_estados_remito
BEGIN
    SELECT RAISE(ABORT, 'El historial de estados del remito no se puede borrar');
END;

-- ---------------------------------------------------------------------------
-- Triggers: agenda sin superposiciones en intervalos [inicio, fin)
-- Los turnos cancelados no ocupan lugar en la agenda.
-- ---------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS turnos_sin_superposicion_insert
BEFORE INSERT ON turnos
WHEN NEW.estado <> 'Cancelado' AND EXISTS (
    SELECT 1 FROM turnos t
    WHERE t.veterinario_id = NEW.veterinario_id
      AND t.estado <> 'Cancelado'
      AND t.inicio < NEW.fin
      AND NEW.inicio < t.fin
)
BEGIN
    SELECT RAISE(ABORT, 'El veterinario ya tiene un turno en ese horario');
END;

CREATE TRIGGER IF NOT EXISTS turnos_sin_superposicion_update
BEFORE UPDATE OF veterinario_id, inicio, fin, estado ON turnos
WHEN NEW.estado <> 'Cancelado' AND EXISTS (
    SELECT 1 FROM turnos t
    WHERE t.id <> NEW.id
      AND t.veterinario_id = NEW.veterinario_id
      AND t.estado <> 'Cancelado'
      AND t.inicio < NEW.fin
      AND NEW.inicio < t.fin
)
BEGIN
    SELECT RAISE(ABORT, 'El veterinario ya tiene un turno en ese horario');
END;
