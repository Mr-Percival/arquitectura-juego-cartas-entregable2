"""Contrato público del núcleo: lo único que un plug-in puede importar."""
from .modelo import (Carta, Combinacion, DecisionFin, EvaluacionCierre, Marcador, Pinta,
                     TipoCombinacion)
from .variante import (GRUPO_ENTRY_POINTS, VERSION_CONTRATO, PoliticaFinPartida, ReglaCierre,
                       TablaPuntos, VariantePlugin)

__all__ = [
    "Carta", "Combinacion", "DecisionFin", "EvaluacionCierre", "Marcador", "Pinta",
    "TipoCombinacion", "GRUPO_ENTRY_POINTS", "VERSION_CONTRATO",
    "PoliticaFinPartida", "ReglaCierre", "TablaPuntos", "VariantePlugin",
]
