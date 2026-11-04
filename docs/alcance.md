# Alcance

Resume la consigna y la presentación del grupo. Ante una diferencia, mandan esos documentos.

## Exigencias de la consigna

- Los 7 procesos obligatorios y todas las validaciones.
- Al menos 2 patrones de diseño.
- Al menos 4 reportes no triviales. La presentación del grupo promete 5.
- El ciclo de vida de la muestra y del remito se evalúa de forma crítica.

## Procesos obligatorios

1. **Clientes:** alta, modificación, baja y consulta, con DNI único.
2. **Mascotas e historias clínicas:** cada mascota tiene un cliente y una especie. Al registrarla se abre su historia clínica.
3. **Consultas y órdenes de derivación:** reserva de turnos, atención (consulta, control o urgencia) con diagnóstico, tratamiento y vacunas, y orden con una o más muestras, que nacen en estado Extraída.
4. **Empaquetado:** las muestras extraídas van a una conservadora disponible y compatible. Se genera el remito y el precinto.
5. **Cadena de envío:** cada despacho, traspaso y arribo se registra con transportista, ubicación, temperatura y responsable.
6. **Recepción:** se registra quién recibe, la temperatura y el precinto. Intacto: se recibe. Roto: se rechaza el remito con todas sus muestras.
7. **Resultados y comprobantes:** resultado por muestra recibida y comprobante con una línea por consulta y por análisis realizado. Las muestras rechazadas no se facturan.

## Validaciones de negocio

- Toda mascota tiene un responsable.
- Una muestra rechazada no admite resultados.
- Los historiales de estado son inmutables: State controla las transiciones y los triggers impiden modificar o borrar.
- Un veterinario no puede tener turnos superpuestos en intervalos `[inicio, fin)`.
- Al registrar una atención se informan las vacunas obligatorias pendientes o vencidas.

## Reportes

1. Atenciones clínicas y derivaciones, por tipo y clínica, filtrable por período.
2. Muestras rechazadas por fallas en el transporte, por clínica y transportista, con remito y precinto.
3. Tratamientos aplicados y vacunas pendientes, con el responsable de cada mascota.
4. Facturación desglosada por clínica, separando consultas y análisis por tipo.
5. Tiempo promedio de tránsito y de procesamiento, calculado desde los historiales.

## Estados

- **Muestra:** Extraída → Empaquetada → En tránsito → Recibida → Analizada. Desde En tránsito también puede pasar a Rechazada.
- **Remito:** Emitido → Despachado → En tránsito → Recibido. Desde En tránsito también puede pasar a Rechazado.

## Fuera del alcance

Son los procesos opcionales de la consigna, excluidos en la presentación:

- Recordatorios de controles, vacunas o resultados.
- Internaciones.
- Stock de conservadoras e insumos médicos.
- Agenda completa de los profesionales del laboratorio.
- Derivaciones para cirugías de alta complejidad.
