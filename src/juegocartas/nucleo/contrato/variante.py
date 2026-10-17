"""Contrato común (SPI) que cumple todo plug-in de reglas (ADR-03).

El núcleo solo conoce estas interfaces. Un plug-in nuevo implementa VariantePlugin
y se declara en el grupo de entry points «juegocartas.variantes»; el núcleo lo
descubre al arrancar sin modificar ni recompilar su código.
"""
from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

from .modelo import Carta, DecisionFin, EvaluacionCierre, Marcador

VERSION_CONTRATO = "1.0"
GRUPO_ENTRY_POINTS = "juegocartas.variantes"


@runtime_checkable
class ReglaCierre(Protocol):
    def evaluar(self, mano: Sequence[Carta]) -> EvaluacionCierre: ...


@runtime_checkable
class TablaPuntos(Protocol):
    def puntos(self, carta: Carta) -> int: ...


@runtime_checkable
class PoliticaFinPartida(Protocol):
    def evaluar(self, marcador: Marcador) -> DecisionFin: ...


@runtime_checkable
class VariantePlugin(Protocol):
    codigo: str
    version_contrato: str

    def esquema_configuracion(self) -> Mapping[str, Any]: ...

    def regla_cierre(self, config: Mapping[str, Any]) -> ReglaCierre: ...

    def tabla_puntos(self, config: Mapping[str, Any]) -> TablaPuntos: ...

    def politica_fin(self, config: Mapping[str, Any]) -> PoliticaFinPartida: ...
