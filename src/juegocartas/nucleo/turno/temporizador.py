"""TurnTimerComponent: provee IProgramarTimeout y avisa ITiempoAgotado al orquestador."""
from __future__ import annotations

import threading
from typing import Callable


class TurnTimer:
    def __init__(self, al_agotarse: Callable[[str, str], None]) -> None:
        self._al_agotarse = al_agotarse
        self._timers: dict[str, threading.Timer] = {}

    def programar(self, partida_id: str, jugador: str, segundos: float) -> None:
        self.cancelar(partida_id)
        timer = threading.Timer(segundos, self._al_agotarse, args=(partida_id, jugador))
        timer.daemon = True
        self._timers[partida_id] = timer
        timer.start()

    def cancelar(self, partida_id: str) -> None:
        timer = self._timers.pop(partida_id, None)
        if timer:
            timer.cancel()
