"""RoundScoringComponent y MatchStandingsComponent."""
from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence

from juegocartas.nucleo.contrato import Carta, DecisionFin, Marcador, VariantePlugin


class IResolverVariante(Protocol):
    def resolver(self, codigo: str) -> VariantePlugin: ...


class RoundScoring:
    """Provee ILiquidarRonda: convierte las manos sobrantes en penalizaciones con la tabla de la variante."""

    def __init__(self, registro: IResolverVariante) -> None:
        self._registro = registro

    def penalizaciones(self, variante: str, config: Mapping[str, Any],
                       sobrantes: Mapping[str, Sequence[Carta]]) -> dict[str, int]:
        tabla = self._registro.resolver(variante).tabla_puntos(config)
        return {jugador: sum(tabla.puntos(c) for c in cartas) for jugador, cartas in sobrantes.items()}


class MatchStandings:
    """Provee IActualizarMarcador: aplica deltas y consulta la política de fin de la variante."""

    def __init__(self, registro: IResolverVariante) -> None:
        self._registro = registro

    def actualizar(self, variante: str, config: Mapping[str, Any], marcador: Marcador,
                   deltas: Mapping[str, int]) -> DecisionFin:
        marcador.aplicar(dict(deltas))
        return self._registro.resolver(variante).politica_fin(config).evaluar(marcador)
