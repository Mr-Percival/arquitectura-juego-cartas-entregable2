"""R8. Fitness function de desempeño (driver Capacidad de respuesta, Entregable 1, Tabla 9).

p95 de la evaluación de cierre < 50 ms sobre 10 000 manos aleatorias de 11 cartas con comodines
(semillas fijas para que la medición sea reproducible).
"""
import time

import pytest

from juegocartas.nucleo.registro.registro import PluginRegistry
from juegocartas.nucleo.turno.repartidor import DeckDealer

MANOS = 10_000
P95_MAXIMO_MS = 50


@pytest.mark.parametrize("codigo", ["CLASICA_433", "APUNTADO_101"])
def test_p95_evaluar_cierre_menor_a_50ms(codigo):
    registro = PluginRegistry()
    registro.descubrir()
    regla = registro.resolver(codigo).regla_cierre({})
    dealer, tiempos = DeckDealer(), []
    for semilla in range(MANOS):
        mano = dealer.repartir(dealer.construir(1, comodines=True), ["j"], 11, semilla)["j"]
        inicio = time.perf_counter()
        regla.evaluar(mano)
        tiempos.append((time.perf_counter() - inicio) * 1000)
    p95 = sorted(tiempos)[int(MANOS * 0.95)]
    print(f"[R8] {codigo}: p95 = {p95:.2f} ms sobre {MANOS} manos")
    assert p95 < P95_MAXIMO_MS, f"p95 = {p95:.1f} ms"
