"""R5. Límite de complejidad ciclomática (McCabe) medido con radon.

Ningún método evaluador de combinaciones (kit del contrato, evaluación y plug-ins de reglas)
puede superar CC = 10. El resto del código tiene un techo de 15 como alerta temprana.
"""
from pathlib import Path

import pytest
from radon.complexity import cc_visit

from conftest import SRC

PAQUETE = SRC / "juegocartas"
EVALUADORES = [PAQUETE / "nucleo" / "contrato" / "combinaciones.py",
               *(PAQUETE / "nucleo" / "evaluacion").rglob("*.py"),
               *(PAQUETE / "plugins").rglob("*.py")]
LIMITE_EVALUADORES = 10
LIMITE_GENERAL = 15


def bloques(archivo: Path):
    for bloque in cc_visit(archivo.read_text(encoding="utf-8")):
        yield bloque
        yield from getattr(bloque, "methods", [])  # radon devuelve las clases con sus métodos aparte


def excesos(archivos, limite):
    return [f"{a.relative_to(SRC)}:{b.lineno} {b.name} CC={b.complexity}"
            for a in archivos for b in bloques(a) if b.complexity > limite]


@pytest.mark.parametrize("archivo", EVALUADORES, ids=lambda p: str(p.relative_to(PAQUETE)))
def test_evaluadores_cc_maximo_10(archivo):
    assert not excesos([archivo], LIMITE_EVALUADORES)


def test_todo_el_codigo_cc_maximo_15():
    assert not excesos(PAQUETE.rglob("*.py"), LIMITE_GENERAL)


def test_radon_detecta_un_metodo_complejo():
    """Prueba de la prueba: una función con 11 ramas debe superar el límite."""
    codigo = "def f(x):\n" + "".join(f"    if x == {i}:\n        return {i}\n" for i in range(11)) + "    return -1\n"
    assert max(b.complexity for b in cc_visit(codigo)) > LIMITE_EVALUADORES
