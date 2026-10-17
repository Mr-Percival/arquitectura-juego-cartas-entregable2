"""Objetos de valor del dominio compartidos entre el núcleo y los plug-ins (sin E/S)."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Pinta(Enum):
    CORAZONES = "H"
    DIAMANTES = "D"
    TREBOLES = "C"
    PICAS = "S"


class TipoCombinacion(Enum):
    GRUPO = "GRUPO"
    ESCALERA = "ESCALERA"


@dataclass(frozen=True)
class Carta:
    """rango 1..13 (As=1, J=11, Q=12, K=13); el comodín no tiene rango ni pinta."""

    rango: int | None
    pinta: Pinta | None
    mazo: int = 1

    @property
    def es_comodin(self) -> bool:
        return self.rango is None

    @staticmethod
    def comodin(mazo: int = 1) -> "Carta":
        return Carta(None, None, mazo)


@dataclass(frozen=True)
class Combinacion:
    tipo: TipoCombinacion
    cartas: tuple[Carta, ...]


@dataclass(frozen=True)
class EvaluacionCierre:
    valida: bool
    tipo: str | None = None  # código definido por el plug-in (p. ej. "TOCAR"); el núcleo no lo interpreta
    combinaciones: tuple[Combinacion, ...] = ()
    sobrantes: tuple[Carta, ...] = ()
    motivo_rechazo: str = ""


@dataclass(frozen=True)
class DecisionFin:
    terminada: bool
    eliminados: tuple[str, ...] = ()
    ganador: str | None = None


@dataclass
class Marcador:
    """Saldo acumulado por jugador (penalizaciones positivas; meta y bonos negativos)."""

    saldos: dict[str, int] = field(default_factory=dict)

    def aplicar(self, deltas: dict[str, int]) -> None:
        for jugador, delta in deltas.items():
            self.saldos[jugador] = self.saldos.get(jugador, 0) + delta
