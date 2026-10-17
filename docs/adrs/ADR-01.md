# ADR-01. Particionamiento arquitectónico superior: por dominio

**Estado:** Aceptado · 2026-09-29 · V-0.0.0.1 · revisado el 2026-10-16 (Entregable 2): **sigue vigente**. El particionamiento por dominio se conserva dentro del *core system* del microkernel (ver ADR-03).

## Contexto
El particionamiento técnico (presentación / negocio / persistencia) agrupa el código por rol técnico. Un cambio de dominio, como agregar el reingreso, atraviesa todas las capas: controlador, servicio, DAO y esquema. Esto contradice el driver de extensibilidad y el principio rector del equipo («una regla, un módulo»). Los cambios esperados del juego son, casi todos, cambios de *reglas* y no de tecnología. Restricciones: equipo de 3 personas, un semestre y un solo cuanto arquitectónico. Alternativas: (a) capas técnicas; (b) particionamiento por dominio; (c) híbrido, con capas técnicas en el primer nivel y subpaquetes por dominio dentro de cada capa.

## Decisión
Se adopta el **particionamiento por dominio** (monolito modular). Los módulos de primer nivel son `sala` (RoomSetup), `turno` (TurnOrchestrator y DeckDealer), `evaluacion` (núcleo de reglas y variantes), `puntuacion` y `soporte` (eventos e historial). Dentro de cada módulo se admite una separación técnica mínima (puertos y adaptadores).

## Justificación
(a) y (c) obligan a que un cambio de regla cruce varias capas. (b) alinea la estructura con la unidad de cambio real (isomorfismo dominio-arquitectura, Richards y Ford, 2025), aísla el núcleo de reglas para probarlo sin infraestructura y deja límites claros para extraer servicios en el futuro si la escalabilidad llegara a ser un driver.

## Consecuencias
- (+) Un cambio de regla toca un solo módulo; el trabajo puede repartirse por subdominio; los límites facilitan las pruebas.
- (−) Las preocupaciones técnicas transversales (serialización, logging) se replican o requieren un módulo de soporte.
- (−) Existe el riesgo de que un módulo «común» se convierta en un cajón de sastre; los desarrolladores acostumbrados a trabajar por capas necesitan disciplina.

## Cumplimiento (Compliance)
*Fitness functions* en CI. Se actualizaron el 2026-10-16: el MVP es en Python, así que se usa PyTestArch en lugar de import-linter, con los nombres reales de los paquetes (`tests/architecture/`).
1. `evaluacion` no importa `turno`, `presentacion` ni `soporte`. Lo cubren R1 y la regla 3.
2. El grafo de componentes no tiene ciclos (R4).
3. `evaluacion` y `puntuacion` no dependen de `turno` ni de `sala`, porque el flujo va de la orquestación hacia el núcleo (`test_reglas_y_puntuacion_no_dependen_de_la_orquestacion`).
4. ~~Acceso solo por paquetes `api`~~: **retirada**. Con el microkernel (ADR-03), la API pública entre el núcleo y los plug-ins es `nucleo.contrato`, que se verifica con R2. Dentro del núcleo, los componentes se comunican por interfaces (`Protocol`), y R6 lo verifica para el orquestador.

El build falla si se viola alguna regla.

## Notas
Relacionado con ADR-02. Se revisará en el Entregable 2 al seleccionar el estilo arquitectónico formal. Alternativa rechazada: arquitectura en capas técnicas pura.
