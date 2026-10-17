"""PluginRegistry: descubre y valida los plug-ins de reglas en tiempo de ejecución (ADR-03)."""
from __future__ import annotations

from importlib.metadata import entry_points
from typing import Iterable

from juegocartas.nucleo.contrato import GRUPO_ENTRY_POINTS, VERSION_CONTRATO, VariantePlugin


class ContratoIncompatible(Exception):
    pass


class VarianteNoRegistrada(KeyError):
    pass


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, VariantePlugin] = {}

    def registrar(self, plugin: VariantePlugin) -> None:
        if not isinstance(plugin, VariantePlugin):
            raise ContratoIncompatible(f"{plugin!r} no implementa VariantePlugin")
        if plugin.version_contrato.split(".")[0] != VERSION_CONTRATO.split(".")[0]:
            raise ContratoIncompatible(f"{plugin.codigo}: contrato {plugin.version_contrato}, núcleo {VERSION_CONTRATO}")
        self._plugins[plugin.codigo] = plugin

    def descubrir(self, fuentes: Iterable | None = None) -> list[str]:
        """Carga los plug-ins instalados que se declaran en el grupo de entry points."""
        fuentes = entry_points(group=GRUPO_ENTRY_POINTS) if fuentes is None else fuentes
        for ep in fuentes:
            self.registrar(ep.load()())
        return sorted(self._plugins)

    def resolver(self, codigo: str) -> VariantePlugin:
        try:
            return self._plugins[codigo]
        except KeyError as exc:
            raise VarianteNoRegistrada(codigo) from exc

    def codigos(self) -> list[str]:
        return sorted(self._plugins)
