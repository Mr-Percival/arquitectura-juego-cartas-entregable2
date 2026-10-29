"""R-11 (sección 4.3). Fin de partida en Apuntado a 101: siempre hay ganador cuando la partida termina."""
from juegocartas.nucleo.contrato import Marcador
from juegocartas.nucleo.puntuacion.liquidador import MatchStandings
from juegocartas.nucleo.registro.registro import PluginRegistry
from juegocartas.plugins.apuntado.plugin import ReglaApuntadoPlugin

CONFIG = {"umbral_eliminacion": 101}


def standings():
    registro = PluginRegistry()
    registro.registrar(ReglaApuntadoPlugin())
    return MatchStandings(registro)


def test_queda_un_solo_vivo_y_gana():
    marcador = Marcador({"a": 90, "b": 95, "c": 40})
    decision = standings().actualizar("APUNTADO_101", CONFIG, marcador, {"a": 20, "b": 10})
    assert decision.terminada and decision.ganador == "c"
    assert set(decision.eliminados) == {"a", "b"}


def test_todos_los_vivos_llegan_a_101_en_la_misma_ronda_gana_el_de_menor_saldo():
    marcador = Marcador({"a": 95, "b": 98})
    decision = standings().actualizar("APUNTADO_101", CONFIG, marcador, {"a": 20, "b": 5})
    assert decision.terminada and decision.ganador == "b"  # 103 frente a 115
    assert decision.eliminados == ("a",)


def test_un_eliminado_de_una_ronda_anterior_no_puede_ganar_el_desempate():
    s, marcador = standings(), Marcador({"a": 50, "b": 60, "c": 70})
    s.actualizar("APUNTADO_101", CONFIG, marcador, {"a": 52})           # a queda en 102: eliminado
    decision = s.actualizar("APUNTADO_101", CONFIG, marcador, {"b": 50, "c": 45})  # b 110, c 115
    assert decision.terminada and decision.ganador == "b"
    assert "a" in decision.eliminados


def test_empate_exacto_gana_el_primero_en_el_orden_del_marcador():
    marcador = Marcador({"a": 95, "b": 95})
    decision = standings().actualizar("APUNTADO_101", CONFIG, marcador, {"a": 10, "b": 10})
    assert decision.terminada and decision.ganador == "a"


def test_la_partida_sigue_si_quedan_dos_o_mas_vivos():
    marcador = Marcador({"a": 30, "b": 40, "c": 50})
    decision = standings().actualizar("APUNTADO_101", CONFIG, marcador, {"a": 80})
    assert not decision.terminada and decision.ganador is None
