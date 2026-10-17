"""Kit de validadores reutilizables que el núcleo ofrece a los plug-ins.

Los plug-ins los componen para armar su regla de cierre; así ningún plug-in
depende de otro (regla de gobernanza R2).
"""
from __future__ import annotations

from itertools import combinations
from typing import Iterator, Sequence

from .modelo import Carta, Combinacion, TipoCombinacion


def es_grupo(cartas: Sequence[Carta]) -> bool:
    """3 o más cartas del mismo rango; los comodines completan."""
    naturales = [c for c in cartas if not c.es_comodin]
    if len(cartas) < 3 or not naturales:
        return False
    return len({c.rango for c in naturales}) == 1


def es_escalera(cartas: Sequence[Carta]) -> bool:
    """3 o más cartas consecutivas de la misma pinta (sin mezclar pintas); los comodines llenan huecos."""
    naturales = sorted((c for c in cartas if not c.es_comodin), key=lambda c: c.rango)
    if len(cartas) < 3 or not naturales:
        return False
    if len({c.pinta for c in naturales}) != 1:
        return False
    rangos = [c.rango for c in naturales]
    if len(set(rangos)) != len(rangos):
        return False
    huecos = (rangos[-1] - rangos[0] + 1) - len(rangos)
    return huecos <= len(cartas) - len(naturales)


def clasificar(cartas: Sequence[Carta]) -> Combinacion | None:
    if es_escalera(cartas):
        return Combinacion(TipoCombinacion.ESCALERA, tuple(cartas))
    if es_grupo(cartas):
        return Combinacion(TipoCombinacion.GRUPO, tuple(cartas))
    return None


def particiones(mano: Sequence[Carta], tamanos: Sequence[int]) -> Iterator[tuple[list[Combinacion], list[Carta]]]:
    """Genera las formas de sacar de la mano combinaciones válidas con los tamaños pedidos.

    Devuelve (combinaciones, sobrantes). La búsqueda está acotada a manos de 11 cartas.
    """
    if not tamanos:
        yield [], list(mano)
        return
    primero, resto = tamanos[0], tamanos[1:]
    for indices in combinations(range(len(mano)), primero):
        combo = clasificar([mano[i] for i in indices])
        if combo is None:
            continue
        restantes = [c for i, c in enumerate(mano) if i not in indices]
        for otras, sobrantes in particiones(restantes, resto):
            yield [combo, *otras], sobrantes
