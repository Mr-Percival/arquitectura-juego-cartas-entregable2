# Risk Storming: respuestas individuales de la fase 1

Cada integrante llenó el kit (`Kit_Risk_Storming_Fase1.pdf`) por separado y sin ver las respuestas de los demás. Escala: impacto y probabilidad de 1 a 3; total = impacto × probabilidad. La consolidación (fase 2) y la mitigación (fase 3) están en la sección 4 del informe.

## Nicolás

| Componente o conexión | Riesgo | Impacto | Probabilidad | Total |
|---|---|---|---|---|
| GameGateway (adaptador WebSocket) | Pérdida de conexión WebSocket por refresco o microcorte del navegador, dejando la sesión desincronizada respecto al estado del orquestador. | 2 | 3 | 6 |
| Flecha TurnTimerComponent → TurnOrchestratorComponent (TiempoAgotado) | Condición de carrera al expirar el tiempo simultáneamente con la recepción del comando de descarte del jugador. | 2 | 2 | 4 |
| TurnOrchestratorComponent | Abandono definitivo de un jugador sin que el orquestador reasigne o termine la partida, bloqueando el avance del resto. | 3 | 2 | 6 |
| LocalEventBus (nucleo.soporte) | Saturación de la cola de eventos internos al notificar múltiples eventos en tiempo real, perdiendo mensajes hacia el Gateway. | 2 | 1 | 2 |
| PostgresRepositoryAdapter | Caída del servidor durante una transacción de la ronda, dejando la base de datos en estado inconsistente. | 3 | 1 | 3 |

## Catalina

| Componente o conexión | Riesgo | Impacto | Probabilidad | Total |
|---|---|---|---|---|
| HandEvaluatorComponent | Fallo en el algoritmo de validación de combinación al evaluar manos complejas que contienen múltiples comodines. | 3 | 2 | 6 |
| Flecha PluginRegistry → ReglaApuntadoPlugin (IResolverVariante) | Excepción no capturada en la lógica propia del plug-in Apuntado (101) al calcular puntos sobrantes menores a 5. | 3 | 1 | 3 |
| RoundScoringComponent / MatchStandingsComponent | Intento simultáneo de cierre de ronda por dos jugadores, provocando un cálculo duplicado o erróneo en el marcador. | 3 | 2 | 6 |
| PluginRegistry | Carga de un plug-in mal versionado o incompatible con la interfaz VariantePlugin en tiempo de arranque. | 3 | 1 | 3 |
| DeckDealerComponent | Sesgo o fallo en el generador pseudoaleatorio al barajar, repartiendo cartas insuficientes o repetidas. | 2 | 1 | 2 |

## Elizabeth

| Componente o conexión | Riesgo | Impacto | Probabilidad | Total |
|---|---|---|---|---|
| RoomSetupComponent | Sobrepasar el límite de jugadores por sala debido a lecturas concurrentes sin bloqueo durante la configuración. | 2 | 2 | 4 |
| Flecha MatchRecordComponent → PostgresRepositoryAdapter (IRepositorioPartidas) | Falla de red hacia PostgreSQL durante la persistencia de la ronda, perdiendo el historial y la puntuación actual. | 3 | 2 | 6 |
| MatchStandingsComponent | Inconsistencia al evaluar el límite de eliminación acumulada de 101 puntos en partidas con desempate. | 3 | 2 | 6 |
| Flecha GameClientUI → GameGateway (ApiPartida) | Envío de peticiones fuera de secuencia (como intentar descartar sin robar) no interceptadas en la capa REST/WebSocket. | 2 | 2 | 4 |
| PostgreSQL | Interbloqueos (deadlocks) al intentar actualizar marcadores e historial de múltiples partidas concurrentes bajo carga alta. | 2 | 1 | 2 |
