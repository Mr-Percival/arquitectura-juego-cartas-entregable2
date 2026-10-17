"""R2. Independencia de reglas de juego y R3. Núcleo agnóstico de variantes (ADR-03).

- Los plug-ins no dependen entre sí.
- Un plug-in solo puede importar el contrato público del núcleo.
- Ningún módulo del núcleo importa un plug-in concreto: los descubre por entry points.
"""
from pytestarch import Rule

from conftest import m

PLUGINS = ["clasica", "apuntado"]


def test_clasica_no_depende_de_apuntado(evaluable):
    (Rule().modules_that().are_sub_modules_of(m("plugins.clasica"))
     .should_not().import_modules_that().are_sub_modules_of(m("plugins.apuntado"))
     .assert_applies(evaluable))


def test_apuntado_no_depende_de_clasica(evaluable):
    (Rule().modules_that().are_sub_modules_of(m("plugins.apuntado"))
     .should_not().import_modules_that().are_sub_modules_of(m("plugins.clasica"))
     .assert_applies(evaluable))


def test_plugins_solo_importan_el_contrato(evaluable):
    for plugin in PLUGINS:
        permitidos = rf"^src\.juegocartas\.(nucleo\.contrato|plugins\.{plugin})(\..+)?$"
        (Rule().modules_that().are_sub_modules_of(m(f"plugins.{plugin}"))
         .should_not().import_modules_except_modules_that().have_name_matching(permitidos)
         .assert_applies(evaluable))


def test_nucleo_no_conoce_plugins_concretos(evaluable):
    (Rule().modules_that().are_sub_modules_of(m("nucleo"))
     .should_not().import_modules_that().are_sub_modules_of(m("plugins"))
     .assert_applies(evaluable))


def test_orquestador_no_conoce_reglas_ni_datos(evaluable):
    """R6. TurnOrchestrator solo habla por interfaces: no importa evaluación, puntuación, registro ni plug-ins."""
    (Rule().modules_that().are_sub_modules_of(m("nucleo.turno"))
     .should_not().import_modules_that()
     .are_sub_modules_of([m("nucleo.evaluacion"), m("nucleo.puntuacion"), m("nucleo.registro"),
                          m("plugins"), m("persistencia")])
     .assert_applies(evaluable))
