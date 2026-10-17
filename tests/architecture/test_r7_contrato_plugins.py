"""R7. Suite de contrato de los plug-ins (cumplimiento de ADR-03).

Todo plug-in descubierto cumple el contrato, y agregar una variante nueva no
requiere tocar el núcleo: basta con exponer un entry point.
"""
import pytest

from juegocartas.nucleo.contrato import Carta, Pinta, VariantePlugin, VERSION_CONTRATO
from juegocartas.nucleo.contrato.combinaciones import es_escalera
from juegocartas.nucleo.registro.registro import ContratoIncompatible, PluginRegistry

H, C, S, D = Pinta.CORAZONES, Pinta.TREBOLES, Pinta.PICAS, Pinta.DIAMANTES


@pytest.fixture(scope="module")
def registro():
    r = PluginRegistry()
    r.descubrir()
    return r


def test_se_descubren_las_dos_variantes(registro):
    assert registro.codigos() == ["APUNTADO_101", "CLASICA_433"]


@pytest.mark.parametrize("codigo", ["APUNTADO_101", "CLASICA_433"])
def test_cada_plugin_cumple_el_contrato(registro, codigo):
    plugin = registro.resolver(codigo)
    assert isinstance(plugin, VariantePlugin)
    config = {k: v["defecto"] for k, v in plugin.esquema_configuracion().items()}
    assert hasattr(plugin.regla_cierre(config), "evaluar")
    assert hasattr(plugin.tabla_puntos(config), "puntos")
    assert hasattr(plugin.politica_fin(config), "evaluar")


def test_escalera_misma_pinta_si_y_pintas_mezcladas_no():
    assert es_escalera([Carta(5, H), Carta(6, H), Carta(7, H)])
    assert not es_escalera([Carta(4, H), Carta(5, C), Carta(6, H)])


def test_clasica_acepta_cuarta_dos_ternas_y_descarte(registro):
    mano = [Carta(3, H), Carta(4, H), Carta(5, H), Carta(6, H),
            Carta(9, H), Carta(9, C), Carta(9, S),
            Carta(12, D), Carta(12, C), Carta(12, S), Carta(2, C)]
    assert registro.resolver("CLASICA_433").regla_cierre({}).evaluar(mano).valida


def test_apuntado_rechaza_tocar_con_sobrante_de_7(registro):
    mano = [Carta(2, H), Carta(3, H), Carta(4, H),
            Carta(8, C), Carta(8, S), Carta(8, D),
            Carta(11, H), Carta(11, C), Carta(11, S),
            Carta(7, D), Carta(13, C)]  # se descarta la K; queda un 7 >= umbral 5
    evaluacion = registro.resolver("APUNTADO_101").regla_cierre({"umbral_tocar": 5}).evaluar(mano)
    assert not evaluacion.valida


def test_variante_nueva_se_registra_sin_tocar_el_nucleo():
    """Simula la instalación de una distribución 'Continental' que expone un entry point."""

    class Continental:
        codigo = "CONTINENTAL"
        version_contrato = VERSION_CONTRATO
        def esquema_configuracion(self): return {}
        def regla_cierre(self, config): ...
        def tabla_puntos(self, config): ...
        def politica_fin(self, config): ...

    class EntryPointFalso:
        def load(self):
            return Continental

    r = PluginRegistry()
    assert r.descubrir([EntryPointFalso()]) == ["CONTINENTAL"]


def test_plugin_con_contrato_de_otra_version_mayor_se_rechaza():
    class Viejo:
        codigo = "VIEJO"
        version_contrato = "0.9"
        def esquema_configuracion(self): return {}
        def regla_cierre(self, config): ...
        def tabla_puntos(self, config): ...
        def politica_fin(self, config): ...

    with pytest.raises(ContratoIncompatible):
        PluginRegistry().registrar(Viejo())
