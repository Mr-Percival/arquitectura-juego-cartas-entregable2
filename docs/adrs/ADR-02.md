# ADR-02. Estrategia de modularidad para la variabilidad de reglas: Strategy en monolito modular

**Estado:** Aceptado · 2026-09-29. **En proceso de reemplazo por ADR-03** (propuesto el 2026-10-16). Pasará a «Reemplazado» cuando el equipo acepte ADR-03. Motivo: se activó el detonante registrado en las Notas, porque el Entregable 2 exige agregar variantes como paquetes aparte, sin alterar el orquestador.

## Contexto
El sistema debe alternar entre Clásica 4-3-3 y Apuntado 101 y admitir reglas opcionales (umbral, comodín, reingreso, apuestas). Opciones evaluadas:
- (a) Condicionales (`if variante == …`) en el motor.
- (b) Patrón Strategy con registro de variantes en el mismo proceso.
- (c) Microkernel con plug-ins cargados en tiempo de ejecución, empaquetados y versionados de forma independiente.

El presupuesto de desempeño del cálculo (< 50 ms, dentro de los 200 ms de respuesta al jugador) y la testabilidad exigen evaluar en memoria.

## Decisión
Se adopta la opción **(b)**. Las interfaces `VarianteJuego`, `ReglaCierre`, `ValidadorCombinacion`, `TablaPuntos` y `PoliticaFinPartida` son el contrato. `RuleVariantRegistry` ensambla la variante desde la `ConfiguracionMesa`, y las reglas opcionales se componen como decoradores (`ValidadorConComodin`, `ReingresoPermitido`).

## Justificación

- (a) viola el principio abierto/cerrado y dispersa las reglas.
- (c) aporta carga dinámica y versionado independiente, capacidades que el MVP no necesita (YAGNI), a cambio de costo de empaquetado, descubrimiento y compatibilidad de contratos.
- (b) cumple los escenarios de extensibilidad y respuesta con la menor complejidad. Como el contrato es idéntico al de un plug-in, migrar a (c) no exige rediseñar.

## Consecuencias
- (+) Agregar una variante es agregar una clase y registrarla; cada estrategia se prueba de forma aislada; no hay costo de latencia.
- (−) Una variante nueva requiere recompilar y redesplegar (no hay carga en caliente).
- (−) El contrato `VarianteJuego` se vuelve una API estable que es costoso cambiar.

## Cumplimiento (Compliance)
1. Prueba de arquitectura: ninguna clase fuera de `evaluacion.variantes` referencia `CierreClasico433` ni `CierreApuntado`.
2. Análisis estático: prohibido comparar el tipo de variante (`switch/if` sobre `TipoVariante`) fuera del registro.
3. Suite de contrato por variante: 5♥ 6♥ 7♥ se acepta como escalera; 4♥ 5♣ 6♥ se rechaza; en Clásica, cuarta + 2 ternas + descarte se acepta; en Apuntado, sobrantes = 7 con umbralTocar = 5 rechaza el Tocar.
4. Prueba de rendimiento: p95 de `evaluarCierre` < 50 ms sobre 10 000 manos aleatorias de 11 cartas con comodín habilitado.

## Notas
Detonante para revisar esta decisión y migrar a microkernel: la necesidad de variantes creadas por terceros o activables sin redespliegue. Relacionado con ADR-01.
