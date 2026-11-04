-- Datos de ejemplo ficticios: catálogos, clínicas, profesionales, clientes y mascotas.
-- Las consultas, muestras y remitos se generan usando el sistema, para que
-- sus historiales de estado queden completos y coherentes.

BEGIN;

INSERT INTO especies (id, nombre) VALUES
    (1, 'Perro'),
    (2, 'Gato');

INSERT INTO vacunas (especie_id, nombre, obligatoria, intervalo_dias) VALUES
    (1, 'Antirrábica', 1, 365),
    (1, 'Séxtuple', 1, 365),
    (1, 'Tos de las perreras', 0, 365),
    (2, 'Antirrábica', 1, 365),
    (2, 'Triple felina', 1, 365),
    (2, 'Leucemia felina', 0, 365);

INSERT INTO clinicas (id, nombre, direccion, telefono) VALUES
    (1, 'Clínica Centro', 'Av. Ejemplo 100, Córdoba', '351-000-0001'),
    (2, 'Clínica Norte', 'Calle Ficticia 200, Córdoba', '351-000-0002');

INSERT INTO veterinarios (clinica_id, matricula, nombre, apellido) VALUES
    (1, 'MP-1001', 'Laura', 'Gómez'),
    (1, 'MP-1002', 'Diego', 'Ferreyra'),
    (2, 'MP-1003', 'Paula', 'Ríos');

INSERT INTO clientes (id, dni, nombre, apellido, telefono, email, direccion) VALUES
    (1, '30000001', 'Ana', 'Martínez', '351-100-0001', 'ana@example.com', 'Calle Uno 111'),
    (2, '30000002', 'Carlos', 'López', '351-100-0002', 'carlos@example.com', 'Calle Dos 222'),
    (3, '30000003', 'Julia', 'Sosa', '351-100-0003', 'julia@example.com', 'Calle Tres 333');

INSERT INTO mascotas (id, cliente_id, especie_id, nombre, raza, sexo, fecha_nacimiento, peso_kg) VALUES
    (1, 1, 1, 'Toby', 'Labrador', 'Macho', '2021-03-15', 28.5),
    (2, 1, 2, 'Mora', 'Común europeo', 'Hembra', '2022-07-02', 4.2),
    (3, 2, 1, 'Luna', 'Caniche', 'Hembra', '2019-11-20', 6.8),
    (4, 3, 2, 'Simón', 'Siamés', 'Macho', '2023-01-10', 3.9);

INSERT INTO historias_clinicas (mascota_id, fecha_apertura, antecedentes) VALUES
    (1, '2026-01-10 09:00', 'Sin antecedentes'),
    (2, '2026-01-10 09:30', 'Alergia alimentaria'),
    (3, '2026-02-05 11:00', 'Cirugía de cadera en 2024'),
    (4, '2026-03-12 16:00', NULL);

INSERT INTO laboratorios (nombre, direccion) VALUES
    ('Laboratorio Central', 'Av. Laboratorio 500, Córdoba');

INSERT INTO tipos_analisis (nombre, tipo_muestra, temp_min, temp_max, precio) VALUES
    ('Hemograma completo', 'Sangre', 2, 8, 18000),
    ('Perfil bioquímico', 'Sangre', 2, 8, 25000),
    ('Urianálisis', 'Orina', 2, 8, 12000),
    ('Coproparasitológico', 'Materia fecal', 2, 8, 10000),
    ('Histopatología', 'Tejido', 15, 25, 40000),
    ('PCR viral', 'Hisopado', -20, -10, 55000);

INSERT INTO conservadoras (codigo, capacidad, temp_min, temp_max, estado) VALUES
    ('REF-01', 10, 2, 8, 'Disponible'),
    ('REF-02', 6, 2, 8, 'Disponible'),
    ('AMB-01', 8, 15, 25, 'Disponible'),
    ('CON-01', 4, -20, -10, 'Disponible'),
    ('REF-03', 10, 2, 8, 'Fuera de servicio');

INSERT INTO transportistas (nombre, cuit, telefono) VALUES
    ('Transporte Ejemplo', '30-00000001-0', '351-200-0001'),
    ('Logística Ficticia', '30-00000002-0', '351-200-0002');

COMMIT;
