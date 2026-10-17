"""R1. Aislamiento de capas: la presentación no accede a la persistencia sin pasar por el núcleo,
y el núcleo no depende de ningún adaptador (puertos y adaptadores, ADR-01 y ADR-04)."""
from pytestarch import Rule

from conftest import m


def test_presentacion_no_accede_a_persistencia(evaluable):
    (Rule().modules_that().are_sub_modules_of(m("presentacion"))
     .should_not().import_modules_that().are_sub_modules_of(m("persistencia"))
     .assert_applies(evaluable))


def test_nucleo_no_depende_de_persistencia(evaluable):
    (Rule().modules_that().are_sub_modules_of(m("nucleo"))
     .should_not().import_modules_that().are_sub_modules_of(m("persistencia"))
     .assert_applies(evaluable))


def test_nucleo_no_depende_de_presentacion(evaluable):
    (Rule().modules_that().are_sub_modules_of(m("nucleo"))
     .should_not().import_modules_that().are_sub_modules_of(m("presentacion"))
     .assert_applies(evaluable))


def test_ningun_modulo_interno_importa_el_adaptador_de_persistencia(evaluable):
    """Nadie dentro de juegocartas importa el adaptador: se inyecta al arrancar (composition root)."""
    (Rule().modules_that().are_sub_modules_of(m("persistencia"))
     .should_not().be_imported_by_modules_that().are_sub_modules_of([m("nucleo"), m("presentacion"), m("plugins")])
     .assert_applies(evaluable))


def test_solo_persistencia_importa_el_driver_de_base_de_datos():
    """Nadie fuera de `persistencia` habla con la base de datos (psycopg, sqlite3, sqlalchemy)."""
    import ast

    from conftest import SRC
    drivers = ("psycopg", "sqlite3", "sqlalchemy")
    paquete = SRC / "juegocartas"
    infractores = []
    for archivo in paquete.rglob("*.py"):
        if "persistencia" in archivo.relative_to(paquete).parts:
            continue
        for nodo in ast.walk(ast.parse(archivo.read_text(encoding="utf-8"))):
            nombres = ([nodo.module or ""] if isinstance(nodo, ast.ImportFrom)
                       else [a.name for a in nodo.names] if isinstance(nodo, ast.Import) else [])
            infractores += [f"{archivo.name}: {n}" for n in nombres if n.split(".")[0] in drivers]
    assert not infractores, infractores


def test_reglas_y_puntuacion_no_dependen_de_la_orquestacion(evaluable):
    """ADR-01, regla 3: el flujo va de la orquestación hacia el núcleo de reglas, nunca al revés."""
    (Rule().modules_that().are_sub_modules_of([m("nucleo.evaluacion"), m("nucleo.puntuacion")])
     .should_not().import_modules_that().are_sub_modules_of([m("nucleo.turno"), m("nucleo.sala")])
     .assert_applies(evaluable))
