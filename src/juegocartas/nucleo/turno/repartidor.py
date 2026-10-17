"""DeckDealerComponent: construye, baraja con semilla y reparte (provee IRepartirMazo)."""
from __future__ import annotations

import random

from juegocartas.nucleo.contrato import Carta, Pinta


class DeckDealer:
    def construir(self, numero_mazos: int = 1, comodines: bool = True) -> list[Carta]:
        mazo: list[Carta] = []
        for m in range(1, numero_mazos + 1):
            mazo += [Carta(r, p, m) for p in Pinta for r in range(1, 14)]
            if comodines:
                mazo += [Carta.comodin(m), Carta.comodin(m)]
        return mazo

    def repartir(self, mazo: list[Carta], jugadores: list[str], cartas: int, semilla: int) -> dict[str, list[Carta]]:
        random.Random(semilla).shuffle(mazo)
        return {j: [mazo.pop() for _ in range(cartas)] for j in jugadores}
