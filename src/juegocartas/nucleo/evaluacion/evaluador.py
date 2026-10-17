"""HandEvaluatorComponent: evalúa una solicitud de cierre con la regla de la variante.

No conoce ninguna variante concreta: pide la regla al registro por código.
"""
from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence

from juegocartas.nucleo.contrato import Carta, EvaluacionCierre, VariantePlugin


class IResolverVariante(Protocol):
    def resolver(self, codigo: str) -> VariantePlugin: ...


class HandEvaluator:
    """Provee IEvaluarMano."""

    def __init__(self, registro: IResolverVariante) -> None:
        self._registro = registro

    def evaluar_cierre(self, variante: str, config: Mapping[str, Any], mano: Sequence[Carta]) -> EvaluacionCierre:
        regla = self._registro.resolver(variante).regla_cierre(config)
        return regla.evaluar(mano)
