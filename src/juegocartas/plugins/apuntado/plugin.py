"""ReglaApuntadoPlugin: 3 ternas + sobrantes < umbralTocar, con penalización acumulada hasta 101.

Solo importa el contrato del núcleo (regla R2: no depende de otros plug-ins).
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from juegocartas.nucleo.contrato import (VERSION_CONTRATO, Carta, DecisionFin, EvaluacionCierre,
                                         Marcador)
from juegocartas.nucleo.contrato.combinaciones import particiones

# Tipos de cierre propios de la variante: los define el plug-in, no el núcleo ni el esquema SQL.
TOCAR, COMPLETO, PINTAS = "TOCAR", "COMPLETO", "PINTAS"


class TablaPuntosEstandar:
    """As, J, Q y K valen 10; del 2 al 10, su valor; el comodín, 0."""

    def puntos(self, carta: Carta) -> int:
        if carta.es_comodin:
            return 0
        return 10 if carta.rango == 1 or carta.rango > 10 else carta.rango


class CierreApuntado:
    def __init__(self, umbral_tocar: int, tabla: TablaPuntosEstandar) -> None:
        self._umbral = umbral_tocar
        self._tabla = tabla

    def evaluar(self, mano: Sequence[Carta]) -> EvaluacionCierre:
        completo = self._completo(mano)
        return completo if completo else self._tocar(mano)

    def _completo(self, mano: Sequence[Carta]) -> EvaluacionCierre | None:
        for combinaciones, sobrantes in particiones(mano, (3, 3, 4)):
            tipo = PINTAS if self._misma_pinta(combinaciones) else COMPLETO
            return EvaluacionCierre(True, tipo, tuple(combinaciones), tuple(sobrantes))
        return None

    def _tocar(self, mano: Sequence[Carta]) -> EvaluacionCierre:
        mejor: EvaluacionCierre | None = None
        for combinaciones, sobrantes in particiones(mano, (3, 3, 3)):
            restantes = sorted(sobrantes, key=self._tabla.puntos)[:-1]  # la más alta se descarta
            puntos = sum(self._tabla.puntos(c) for c in restantes)
            if puntos < self._umbral:
                mejor = EvaluacionCierre(True, TOCAR, tuple(combinaciones), tuple(restantes))
                break
        return mejor or EvaluacionCierre(False, motivo_rechazo=f"Sobrantes >= {self._umbral} puntos o faltan ternas")

    @staticmethod
    def _misma_pinta(combinaciones) -> bool:
        pintas = {c.pinta for combo in combinaciones for c in combo.cartas if not c.es_comodin}
        return len(pintas) == 1


class UmbralEliminacion:
    def __init__(self, umbral: int) -> None:
        self._umbral = umbral

    def evaluar(self, marcador: Marcador) -> DecisionFin:
        eliminados = tuple(j for j, s in marcador.saldos.items() if s >= self._umbral)
        vivos = [j for j in marcador.saldos if j not in eliminados]
        if len(vivos) <= 1:
            return DecisionFin(True, eliminados, vivos[0] if vivos else None)
        return DecisionFin(False, eliminados)


class ReglaApuntadoPlugin:
    codigo = "APUNTADO_101"
    version_contrato = VERSION_CONTRATO

    def esquema_configuracion(self) -> Mapping[str, Any]:
        return {
            "umbral_tocar": {"tipo": int, "defecto": 5},
            "umbral_eliminacion": {"tipo": int, "defecto": 101},
            "bono_completo": {"tipo": int, "defecto": 10},
            "bono_pintas": {"tipo": int, "defecto": 25},
            "comodines_habilitados": {"tipo": bool, "defecto": True},
            "tiempo_limite_turno_s": {"tipo": int, "defecto": 60},
        }

    def regla_cierre(self, config: Mapping[str, Any]) -> CierreApuntado:
        return CierreApuntado(config.get("umbral_tocar", 5), TablaPuntosEstandar())

    def tabla_puntos(self, config: Mapping[str, Any]) -> TablaPuntosEstandar:
        return TablaPuntosEstandar()

    def politica_fin(self, config: Mapping[str, Any]) -> UmbralEliminacion:
        return UmbralEliminacion(config.get("umbral_eliminacion", 101))
