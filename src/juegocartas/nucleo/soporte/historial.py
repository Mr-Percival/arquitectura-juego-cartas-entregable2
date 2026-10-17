"""MatchRecordComponent y su puerto de salida IRepositorioPartidas.

El núcleo define el puerto; el adaptador de PostgreSQL (paquete persistencia) lo
implementa. Así el núcleo nunca importa la base de datos (regla R1).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CierreRonda:
    partida_id: str
    ronda_id: str
    jugador_cierra: str
    tipo_cierre: str
    penalizaciones: dict[str, int]
    bonificaciones: dict[str, int]
    eliminados: tuple[str, ...]
    partida_terminada: bool
    ganador: str | None
    comando_id: str
    numero_turno: int


class RondaYaLiquidada(Exception):
    """Otro jugador cerró primero: la transacción encontró la ronda en estado LIQUIDADA."""


class IRepositorioPartidas(Protocol):
    def liquidar_ronda(self, cierre: CierreRonda) -> None:
        """Escribe todo el cierre en UNA transacción (ver sección 2.4)."""

    def historial(self, partida_id: str) -> list[dict]: ...


class MatchRecord:
    """Provee IRegistrarRonda e IConsultarHistorial; requiere IRepositorioPartidas."""

    def __init__(self, repositorio: IRepositorioPartidas) -> None:
        self._repo = repositorio

    def registrar_ronda(self, cierre: CierreRonda) -> None:
        self._repo.liquidar_ronda(cierre)

    def consultar_historial(self, partida_id: str) -> list[dict]:
        return self._repo.historial(partida_id)
