# ADR-03. Estilo arquitectónico: microkernel con plug-ins de reglas descubiertos en tiempo de ejecución

**Estado:** Aceptado · 2026-10-27 · V-0.0.1.0 · aprobado por el equipo. **Reemplaza a ADR-02**.

## Contexto
El Entregable 2 exige incorporar o modificar variantes de juego (por ejemplo, Continental o Póker) **sin recompilar ni alterar el orquestador de turnos ni la persistencia**. ADR-02 resolvió la variabilidad con el patrón Strategy dentro del monolito modular, pero aceptó como consecuencia que una variante nueva requiere reconstruir y redesplegar el monolito. También dejó registrado su detonante de cambio: «variantes creadas por terceros o activables sin redespliegue». El requisito de la guía equivale a la primera condición: una variante debe poder llegar como un paquete aparte, sin tocar el artefacto del núcleo.

Los drivers del Entregable 1 siguen vigentes:
- Extensibilidad: una regla nueva cabe en un módulo y no hace cambios en TurnOrchestrator.
- Testabilidad: ≥ 90 % de cobertura de ramas en el núcleo de reglas.
- Capacidad de respuesta: p95 de la acción a la pantalla < 200 ms y `evaluarCierre` < 50 ms.

Restricciones: equipo de 3 personas, un semestre, un solo cuanto arquitectónico y un MVP en Python.

Alternativas (sección 1.1):
- (a) Monolito modular con Strategy (ADR-02).
- (b) Microkernel en un solo proceso, con plug-ins descubiertos al arrancar.
- (c) Service-based, con un servicio de reglas separado.

## Decisión
Se adopta **(b)**.

**Core system.** Lo forman `nucleo.sala`, `nucleo.turno` (orquestador, repartidor y temporizador), `nucleo.evaluacion`, `nucleo.puntuacion`, `nucleo.registro` y `nucleo.soporte`. Conserva el particionamiento por dominio de ADR-01.

**Contrato.** El contrato común es `VariantePlugin` (versión 1.0; 1.1 desde el 29-10-2026, que agrega `Marcador.eliminados` y es compatible con los plug-ins 1.x), en `juegocartas.nucleo.contrato`, con estas operaciones: `codigo`, `version_contrato`, `esquema_configuracion()`, `regla_cierre(cfg)`, `tabla_puntos(cfg)` y `politica_fin(cfg)`. El contrato incluye además un kit de validadores reutilizables (grupo, escalera, comodín y búsqueda de particiones).

**Plug-ins.** `ReglaClasicaPlugin` y `ReglaApuntadoPlugin`. Cada uno importa solo el contrato.

**Registro.** `PluginRegistry` descubre los plug-ins al arrancar en el grupo de *entry points* `juegocartas.variantes` y rechaza los que tengan una versión mayor de contrato incompatible. El registro no accede a la base de datos: el *composition root* le entrega la lista al repositorio, que la registra en la tabla `variante`. El núcleo invoca a los plug-ins con llamadas en memoria a través del contrato, nunca de forma remota.

**Cómo se agrega una variante nueva (por ejemplo, Continental):**
1. Se crea la distribución `juegocartas-continental`, con una clase que implementa `VariantePlugin`.
2. En su `pyproject.toml` se declara `[project.entry-points."juegocartas.variantes"] CONTINENTAL = "juegocartas_continental:Plugin"`.
3. Se instala con `pip install` en el entorno del servidor y se reinicia el proceso.
4. El registro la descubre y el repositorio la registra en `variante`. Sus parámetros viajan en `parametro_partida` y sus códigos de tipo de cierre van en `ronda.tipo_cierre`, que no tiene CHECK fijo.

El artefacto del núcleo no se modifica, no se reconstruye ni se redespliega (solo se reinicia el proceso), y el esquema no se migra. En Python no hay compilación: la diferencia con ADR-02 está en que la variante es un artefacto separado del núcleo.

## Justificación
En la matriz ponderada de la sección 1.1 (p95 medido de la evaluación: 5,2 ms), el microkernel obtiene 4,65 de 5, frente a 4,15 del monolito modular y 3,05 de service-based.
- Es el único que cumple de forma literal el requisito de «sin recompilar ni alterar el orquestador»: el núcleo nunca importa un plug-in, y eso lo verifica la regla R3.
- Mantiene la evaluación en memoria (capacidad de respuesta).
- La suite de contrato prueba cada plug-in de forma aislada (testabilidad).

Service-based agrega un salto de red en cada cierre, una base de datos compartida y un costo operativo que el MVP no necesita. El monolito modular ya fue descartado por el detonante de ADR-02.

## Consecuencias
**Positivas:**
- Agregar una variante es agregar un paquete.
- Las reglas evolucionan sin tocar el núcleo, la persistencia ni la UI.
- El contrato fuerza el bajo acoplamiento.

**Negativas:**
- El contrato `VariantePlugin` se convierte en una API pública. Cambiarlo exige versionarlo (SemVer) y mantener la compatibilidad de la versión mayor.
- Los plug-ins corren en el mismo proceso, sin aislamiento: un plug-in defectuoso puede degradar el servidor. Se mitiga con una lista de plug-ins permitidos en la configuración y con la suite de contrato obligatoria.
- Activar una variante exige reiniciar el proceso; no hay carga en caliente en el MVP.
- Un descubrimiento mal configurado deja variantes sin registrar. Se mitiga con una prueba de arranque que verifica los códigos esperados.

## Cumplimiento (Compliance)
*Fitness functions* en `tests/architecture/`, ejecutadas en CI (`.github/workflows/fitness-functions.yml`). El build falla si alguna se viola.
- **R2:** `plugins.clasica` y `plugins.apuntado` no se importan entre sí, y cada plug-in importa solo `nucleo.contrato` (PyTestArch).
- **R3:** ningún módulo de `nucleo` importa `plugins`.
- **R6:** `nucleo.turno` no importa `evaluacion`, `puntuacion`, `registro`, `plugins` ni `persistencia`.
- **R7:** suite de contrato.
  - Cada plug-in descubierto cumple `VariantePlugin`.
  - 5♥ 6♥ 7♥ es escalera y 4♥ 5♣ 6♥ no lo es.
  - Clásica acepta 1 cuarta + 2 ternas + 1 descarte.
  - Apuntado rechaza el Tocar cuando el sobrante es 7.
  - Una variante «Continental» simulada se registra solo con un *entry point*.
  - Un contrato de otra versión mayor se rechaza.
- **R5:** CC ≤ 10 en los evaluadores (radon).
- **R8:** p95 de la evaluación de cierre < 50 ms sobre 10 000 manos.

## Notas
- Autores: C. Arango Sierra, E. Alzate Zapata y N. Meza Ortega.
- Fecha de la propuesta: 16-10-2026. Aceptado: 27-10-2026. Última modificación: 27-10-2026.
- Reemplaza a ADR-02. Complementa a ADR-01, que sigue vigente dentro del núcleo. Relacionado con ADR-04, porque el esquema es agnóstico de la variante, y con ADR-05.
- Detonante para revisar esta decisión: necesitar plug-ins de terceros no confiables (aislamiento por proceso o *sandbox*) o activarlos sin reiniciar (carga en caliente).
