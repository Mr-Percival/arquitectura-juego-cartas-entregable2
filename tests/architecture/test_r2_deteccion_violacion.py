"""Prueba de la prueba para R2: si un plug-in importa a otro, la fitness function debe fallar.

Copia el código a un directorio temporal, inyecta la violación y comprueba que PyTestArch la detecta.
"""
import shutil

import pytest
from pytestarch import Rule

from conftest import SRC, evaluable_de, m


def test_r2_detecta_import_entre_plugins(tmp_path):
    copia = tmp_path / "src"
    shutil.copytree(SRC / "juegocartas", copia / "juegocartas", ignore=shutil.ignore_patterns("__pycache__"))
    plugin = copia / "juegocartas" / "plugins" / "clasica" / "plugin.py"
    plugin.write_text(plugin.read_text(encoding="utf-8")
                      + "\nfrom juegocartas.plugins.apuntado.plugin import TablaPuntosEstandar\n", encoding="utf-8")
    regla = (Rule().modules_that().are_sub_modules_of(m("plugins.clasica"))
             .should_not().import_modules_that().are_sub_modules_of(m("plugins.apuntado")))
    with pytest.raises(AssertionError):
        regla.assert_applies(evaluable_de(copia))
