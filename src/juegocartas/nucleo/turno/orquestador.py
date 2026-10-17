"""TurnOrchestratorComponent: único mediador del flujo de turno (FSM).

Solo conoce interfaces (IEvaluarMano, ILiquidarRonda, IRegistrarRonda, IPublicarEvento).
No importa plug-ins, ni la base de datos, ni la presentación (reglas R1, R3 y R6).
Sección 2.4, capa 1: un candado por partida envuelve TODO el cierre (validar, evaluar,
liquidar, persistir y publicar). ADR-05: el evento se publica solo si la persistencia confirmó.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Protocol, Sequence

from juegocartas.nucleo.contrato import Carta, EvaluacionCierre


class FaseTurno(Enum):
    ESPERANDO_ROBO = "ESPERANDO_ROBO"
    ESPERANDO_DESCARTE = "ESPERANDO_DESCARTE"
    FINALIZADO = "FINALIZADO"


class IEvaluarMano(Protocol):
    def evaluar_cierre(self, variante: str, config: Mapping[str, Any], mano: Sequence[Carta]) -> EvaluacionCierre: ...


class ILiquidarRonda(Protocol):
    def liquidar(self, partida_id: str, quien_cierra: str, evaluacion: EvaluacionCierre) -> Any:
        """Devuelve el CierreRonda listo para persistir (penalizaciones, eliminados, fin)."""


class IRegistrarRonda(Protocol):
    def registrar_ronda(self, cierre: Any) -> None: ...


class IPublicarEvento(Protocol):
    def publicar(self, evento: Any) -> None: ...


class ComandoFueraDeTurno(Exception):
    pass


@dataclass
class EstadoTurno:
    variante: str
    config: Mapping[str, Any]
    en_turno: str
    fase: FaseTurno = FaseTurno.ESPERANDO_ROBO
    candado: threading.Lock = field(default_factory=threading.Lock)


class TurnOrchestrator:
    """Provee IComandosTurno."""

    def __init__(self, evaluador: IEvaluarMano, liquidador: ILiquidarRonda,
                 registro: IRegistrarRonda, eventos: IPublicarEvento) -> None:
        self._evaluador = evaluador
        self._liquidador = liquidador
        self._registro = registro
        self._eventos = eventos
        self._partidas: dict[str, EstadoTurno] = {}

    def iniciar(self, partida_id: str, variante: str, config: Mapping[str, Any], primero: str) -> None:
        self._partidas[partida_id] = EstadoTurno(variante, config, primero)

    def robar(self, partida_id: str, jugador: str) -> None:
        estado = self._partidas[partida_id]
        with estado.candado:
            self._exigir(estado, jugador, FaseTurno.ESPERANDO_ROBO)
            estado.fase = FaseTurno.ESPERANDO_DESCARTE

    def solicitar_cierre(self, partida_id: str, jugador: str, mano: Sequence[Carta]) -> EvaluacionCierre:
        estado = self._partidas[partida_id]
        with estado.candado:
            self._exigir(estado, jugador, FaseTurno.ESPERANDO_DESCARTE)
            evaluacion = self._evaluador.evaluar_cierre(estado.variante, estado.config, mano)
            if not evaluacion.valida:
                return evaluacion
            cierre = self._liquidador.liquidar(partida_id, jugador, evaluacion)
            self._registro.registrar_ronda(cierre)  # si falla, la excepción sale y no se publica nada
            estado.fase = FaseTurno.FINALIZADO
            self._eventos.publicar({"tipo": "RondaLiquidada", "partida_id": partida_id, "cerrada_por": jugador})
            return evaluacion

    @staticmethod
    def _exigir(estado: EstadoTurno, jugador: str, fase: FaseTurno) -> None:
        if jugador != estado.en_turno or estado.fase is not fase:
            raise ComandoFueraDeTurno(f"{jugador} no puede actuar en la fase {estado.fase.value}")
