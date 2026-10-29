# ADR-04. Motor y modelo de persistencia: PostgreSQL relacional (3FN) en una base de datos centralizada

**Estado:** Aceptado · 2026-10-27 · V-0.0.1.0 · aprobado por el equipo. Reemplaza la propuesta preliminar del C4 del Entregable 1 («Archivos JSON / BD documental»).

## Contexto
El sistema debe persistir:
- Sesiones, salas, jugadores y manos.
- La trazabilidad de robos, descartes y estados de ronda.
- El historial de penalizaciones y los marcadores.

Debe representar con el mismo modelo dos tipos de partida:
- Atómicas: Clásica, de 1 ronda y sin historial de penalizaciones.
- Multironda: Apuntado, con penalizaciones acumuladas hasta 101.

Al cerrar una ronda, la liquidación debe ser **atómica**: dos jugadores no pueden cerrar la misma ronda ni pueden quedar penalizaciones parciales.

Por ADR-03, agregar una variante no puede cambiar la persistencia.

Hay un solo cuanto arquitectónico y unas 20 partidas concurrentes en el MVP.

Alternativas:
- (a) SQLite embebida.
- (b) PostgreSQL centralizada.
- (c) Base documental (MongoDB), con el agregado Partida embebiendo sus rondas, jugadas y puntajes.

## Decisión
Se adopta **(b): PostgreSQL 16, con un esquema relacional en 3FN** de 14 tablas (`docs/modelos/sql/esquema.sql`), en una topología de **base de datos monolítica centralizada** compartida por todo el núcleo.

**Acceso.** Solo el adaptador `PostgresRepositoryAdapter` habla con la base de datos, a través del puerto `IRepositorioPartidas` que define el núcleo. Los plug-ins nunca acceden a los datos: el núcleo les entrega lo que necesitan, como en el microkernel de Richards y Ford (2025).

**Variabilidad sin migraciones.** Se resuelve con dos tablas:
- `variante`: catálogo de plug-ins.
- `parametro_partida`: clave y valor validados contra `esquema_configuracion()` del plug-in.

## Justificación
**Ventajas de PostgreSQL (b):**
- **Atomicidad del cierre.** Las transacciones ACID con bloqueo de fila (`SELECT … FOR UPDATE` sobre la ronda) serializan cierres simultáneos sin bloquear otras partidas. Se probó contra PostgreSQL 16 real: de dos cierres concurrentes, uno se acepta y el otro se rechaza sin escribir nada.
- **Invariantes declarativos que no dependen del código.** Algunos ejemplos:
  - Índice único parcial: una sola ronda `EN_JUEGO` por partida.
  - PK (`ronda_id`, `jugador_id`) en `puntaje_ronda`: impide liquidar dos veces la misma ronda.
  - FK compuesta: solo un participante puede cerrar.
  - CHECK: estados y penalizaciones no negativas.
  - UNIQUE `comando_id`: idempotencia de los comandos.
- **Consultas analíticas** del historial y del marcador con SQL estándar (funciones de ventana).

**Por qué no SQLite (a):** es más simple y aguantaría la carga del MVP, pero no tiene `SELECT … FOR UPDATE`, bloquea toda la base en cada escritura y su archivo local impide correr más de una instancia del servidor.

**Por qué no la base documental (c):** encaja bien con el agregado Partida y ofrece índices únicos por colección y transacciones multidocumento (desde la versión 4.0), pero tiene tres problemas:
- No tiene integridad referencial (FK).
- No se pueden declarar restricciones sobre los subdocumentos embebidos, como «una ronda abierta».
- Los marcadores globales y el historial por jugador cruzan documentos, y la bitácora de jugadas hace crecer el documento de la partida.

## Consecuencias
**Positivas:**
- La integridad está garantizada en dos niveles: núcleo y base de datos.
- El historial completo sirve para auditar reclamos.
- El esquema no cambia con las variantes.

**Negativas:**
- Hay que operar un proceso adicional (frente a SQLite).
- El mapeo objeto-relacional exige escribir el *data mapper* (sección 2.3).
- Los cambios del núcleo requieren migraciones versionadas.
- `puntaje_acumulado.total` es redundante con la suma de `puntaje_ronda`. La redundancia es controlada: se escribe en la misma transacción y se verifica con `v_inconsistencias_marcador`.
- `parametro_partida` guarda los valores como texto, así que el tipo se valida en la aplicación (RoomSetup) y no en la base.
- `ronda.tipo_cierre` no tiene CHECK porque cada plug-in define sus códigos.
- `mano_jugador`, `puntaje_ronda` y `partida.ganador_id` referencian `jugador` y no `participacion`, para no romper la 3FN; la pertenencia a la partida la valida el núcleo.

## Cumplimiento (Compliance)
- **R1:** el `nucleo` y la `presentacion` no importan `persistencia` (PyTestArch).
- **Pruebas de integración** contra PostgreSQL 16 (`tests/integracion/`, con pgserver):
  - Partida Apuntado de 3 rondas que acumula y elimina a 101.
  - Partida Clásica de una sola ronda.
  - Dos cierres simultáneos: solo uno gana.
  - Un fallo a mitad del cierre no deja escrituras parciales.
  - No puede haber dos rondas abiertas.
- **Fitness function de datos:** `v_inconsistencias_marcador` debe devolver 0 filas. Se verifica en las pruebas de integración y, en producción, con una tarea programada diaria.
- **Revisión en el PR:** si el PR de una variante nueva modifica `esquema.sql`, viola esta decisión y debe rechazarse.

## Notas
- Autores: C. Arango Sierra, E. Alzate Zapata y N. Meza Ortega.
- Fecha de la propuesta: 16-10-2026. Aceptado: 27-10-2026. Última modificación: 27-10-2026.
- Relacionado con ADR-03 (agnosticismo de la variante) y ADR-05 (los eventos se publican después del *commit*).
- Detonante para revisar esta decisión: escalar a varios cuantos (base de datos por servicio) o tener una carga de lectura de historiales que justifique réplicas de lectura.
