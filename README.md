# Sistema Digital de Juego de Cartas: Entregable 2

Fundamentos de Arquitectura de Software, 2026-2, Universidad Nacional de Colombia, sede Medellín.
Equipo «Los Fabulosos Cadillacs»: Catalina Arango Sierra, Elizabeth Alzate Zapata y Nicolas Meza Ortega.

Arquitectura **microkernel**: un núcleo (sala, turnos, evaluación, puntuación, registro y soporte) más plug-ins de reglas (Clásica 4-3-3 y Apuntado a 101), descubiertos por *entry points*. Los datos se guardan en PostgreSQL con un esquema en 3FN.

## Estructura

```
docs/
  adrs/                ADR-01 a ADR-05 (.md)
  modelos/
    plantuml/          componentes, relacional físico, clases de persistencia, secuencia de cierre
    er/                E-R en notación de Barker (lo genera herramientas/generar_er_barker.py)
    sql/               esquema.sql (DDL) y datos_iniciales.sql
  informe/             Entregable2.html → Entregable2.pdf (build_pdf.py)
  risk_storming/       kit de la sesión y resultados
src/juegocartas/
  nucleo/              core system (contrato, sala, turno, evaluacion, puntuacion, registro, soporte)
  plugins/             clasica, apuntado (solo importan nucleo.contrato)
  presentacion/        GameGateway
  persistencia/        PostgresRepositoryAdapter
tests/
  architecture/        fitness functions R1–R8 (PyTestArch, ast, radon, pytest)
  integracion/         esquema y transacciones sobre PostgreSQL 16 (pgserver)
```

## Ejecutar las fitness functions

```bash
python -m venv .venv
.venv/Scripts/activate        # en Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
pytest tests -v               # 44 pruebas (R1–R9 + integración PostgreSQL)
radon cc src -s -a            # reporte de complejidad ciclomática
```

En CI corren con `.github/workflows/fitness-functions.yml`, en cada *push* y en cada *pull request*.

## Agregar una variante sin tocar el núcleo (ADR-03)

1. Crea un paquete que implemente `juegocartas.nucleo.contrato.VariantePlugin`.
2. Declara el *entry point* en su `pyproject.toml`:

   ```toml
   [project.entry-points."juegocartas.variantes"]
   CONTINENTAL = "juegocartas_continental:Plugin"
   ```

3. Instálalo con `pip install` y reinicia el servidor. `PluginRegistry` lo descubre al arrancar.

## Regenerar diagramas y PDF

```bash
# Requiere herramientas/plantuml.jar (https://github.com/plantuml/plantuml/releases, v1.2024.7) y Java
java -jar herramientas/plantuml.jar -tsvg -o ../../informe/build docs/modelos/plantuml/*.puml
python herramientas/generar_er_barker.py
java -jar herramientas/plantuml.jar -tsvg -o ../../informe/build docs/modelos/er/er_barker.puml
python docs/informe/build_pdf.py
```
