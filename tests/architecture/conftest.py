"""Configuración compartida de las fitness functions de arquitectura (Richards y Ford, 2025, cap. 6)."""
from pathlib import Path

import pytest
from pytestarch import EvaluableArchitecture, get_evaluable_architecture

SRC = Path(__file__).resolve().parents[2] / "src"
RAIZ = "src.juegocartas"  # nombre con que PyTestArch registra el paquete raíz


def evaluable_de(src: Path) -> EvaluableArchitecture:
    return get_evaluable_architecture(src, src / "juegocartas", exclusions=("*__pycache__*",))


@pytest.fixture(scope="session")
def evaluable() -> EvaluableArchitecture:
    return evaluable_de(SRC)


def m(nombre: str) -> str:
    """Nombre completo de un módulo: m('nucleo.turno') -> 'src.juegocartas.nucleo.turno'."""
    return f"{RAIZ}.{nombre}"
