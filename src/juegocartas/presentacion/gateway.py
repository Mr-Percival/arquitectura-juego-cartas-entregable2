"""GameGateway: adaptador de entrada (REST + WebSocket en el MVP).

Solo habla con el núcleo a través de sus interfaces de servicio; no importa
persistencia ni entidades de base de datos (regla R1).
"""
from __future__ import annotations

from typing import Any, Mapping

from juegocartas.nucleo.soporte.eventos import EventoPartida, LocalEventBus
from juegocartas.nucleo.turno.orquestador import TurnOrchestrator


class GameGateway:
    def __init__(self, orquestador: TurnOrchestrator, eventos: LocalEventBus) -> None:
        self._orquestador = orquestador
        self._conexiones: dict[str, list] = {}
        for tipo in ("CartaDescartada", "TurnoCambiado", "RondaLiquidada", "PartidaFinalizada"):
            eventos.suscribir(tipo, self._difundir)

    def _difundir(self, evento: EventoPartida) -> None:
        for conexion in self._conexiones.get(evento.partida_id, []):
            conexion.append({"tipo": evento.tipo, **evento.datos})  # en el MVP: websocket.send_json

    def comando(self, partida_id: str, payload: Mapping[str, Any]) -> dict:
        raise NotImplementedError("Se implementa en el MVP (Entregable 3)")
