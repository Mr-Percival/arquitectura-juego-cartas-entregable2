# ADR-05. Sincronización de turnos y comunicación entre componentes: comandos síncronos en memoria y eventos locales para notificar

**Estado:** Aceptado · 2026-10-27 · V-0.0.1.0 · aprobado por el equipo.

## Contexto
Hay dos tipos de interacción con necesidades distintas:

1. **Comandos que cambian el estado:** robar, descartar y solicitar cierre. El jugador necesita un veredicto inmediato (aceptado o rechazado con su motivo, visible en menos de 100 ms). Además, el orden de los comandos dentro de una partida debe ser estricto (invariante robar → combinar → descartar → ceder), y el cierre debe persistirse de forma atómica (ADR-04).
2. **Notificaciones a los demás:** carta descartada, cambio de turno, ronda liquidada y partida finalizada. Deben llegar a los clientes por WebSocket sin que el núcleo conozca la presentación (regla R1).

Restricciones:
- Un solo proceso y un solo cuanto (ADR-03).
- Responsiveness: p95 < 200 ms.
- El servidor es la fuente de verdad del estado.

Alternativas:
- (a) Todo síncrono: el orquestador llama directamente al gateway para notificar.
- (b) Todo por eventos, con comandos asíncronos en una cola.
- (c) Híbrido: comandos síncronos en memoria a través de interfaces y notificaciones como eventos locales en proceso.
- (d) Un broker externo (Redis o RabbitMQ).

## Decisión
Se adopta **(c)**.

**Comandos.** Entran por `GameGateway` y siguen este recorrido: `IComandosTurno` → `TurnOrchestrator`, que invoca de forma síncrona `IEvaluarMano`, `ILiquidarRonda` e `IRegistrarRonda`.

**Serialización por partida.** Cada partida tiene su propio candado (`threading.Lock`; un `asyncio.Lock` en el servidor ASGI). Así, una partida procesa sus comandos de uno en uno, y partidas distintas avanzan en paralelo.

**Idempotencia.** Cada comando lleva un `comando_id` único. Si el cliente reintenta un comando, este no se aplica dos veces.

**Notificaciones.** El orquestador publica `EventoPartida` (`CartaDescartada`, `TurnoCambiado`, `RondaLiquidada` y `PartidaFinalizada`) en `LocalEventBus` **solo después del *commit***. `GameGateway` se suscribe y difunde los eventos por WebSocket. Si un suscriptor falla, su error se aísla y no afecta el turno.

**Reconexión.** Si el jugador refresca el navegador, el cliente recupera su sesión (tabla `sesion`) y pide una instantánea del estado. No se reproducen eventos perdidos.

## Justificación
- **(a)** obligaría al núcleo a importar la presentación, lo que viola R1, y acopla la latencia del turno al envío por red a cada cliente.
- **(b)** vuelve eventual el veredicto de una jugada. Complica entregar el motivo del rechazo en menos de 100 ms y las pruebas deterministas, y no aporta nada mientras exista un solo cuanto.
- **(d)** suma infraestructura y un salto de red sin necesidad (YAGNI).
- **(c)** da latencia en memoria, orden estricto por partida y desacoplamiento entre el núcleo y la presentación, con el menor costo.

## Consecuencias
**Positivas:**
- El veredicto es inmediato y el código es simple de probar.
- El núcleo no conoce la presentación.
- Se pueden agregar suscriptores (bitácora, métricas) sin tocar el orquestador.

**Negativas:**
- Los eventos viven en memoria. Si el proceso cae después del *commit* y antes de publicar, los clientes se pierden esa notificación; se mitiga con la reconexión por instantánea (el estado correcto ya está en la base de datos).
- El candado por partida limita una partida a un comando a la vez. Es aceptable porque los turnos son secuenciales.
- Escalar a varias instancias exigiría un bus externo y afinidad de partida: es el detonante de (d).

## Cumplimiento (Compliance)
**Automatizado hoy:**
- **R1:** `nucleo` no importa `presentacion` (PyTestArch).
- **R6:** `nucleo.turno` solo depende de interfaces.
- **R9** (`test_r9_orquestacion_cierre.py`):
  - El evento se publica después de persistir.
  - Si la persistencia falla, el evento no se publica.
  - De dos cierres simultáneos en la misma partida, solo uno persiste.
- `comando_id UNIQUE` y la prueba de cierre concurrente en `tests/integracion/`.

**Planificado para el MVP (Entregable 3):**
- Prueba de rendimiento: p95 del comando al evento recibido < 200 ms con 20 partidas simultáneas.
- Mitigación de R-01 (Risk Storming, sección 4.3 del informe): cada partida lleva un número de versión que aumenta con cada comando aceptado y viaja en cada evento. Si el cliente detecta un hueco o se reconecta, pide la instantánea. Los comandos llevan `comando_id`, así que reintentarlos es seguro.
- Mitigación de R-03: al agotarse el tiempo, el aviso de `TurnTimer` pasa por el mismo candado de la partida y el orquestador juega de forma automática (roba y descarta la carta robada). Tras 2 tiempos agotados seguidos, el jugador pasa a `ABANDONO` (estado ya agregado al CHECK de `participacion.estado_jugador`) y se salta en la rotación.

## Notas
- Autores: C. Arango Sierra, E. Alzate Zapata y N. Meza Ortega.
- Fecha de la propuesta: 16-10-2026. Aceptado: 27-10-2026. Última modificación: 29-10-2026 (mitigaciones de R-01 y R-03).
- Relacionado con ADR-03 (un solo proceso) y ADR-04 (los eventos se publican después del *commit*).
- Detonante para revisar esta decisión: desplegar más de una instancia del servidor.
