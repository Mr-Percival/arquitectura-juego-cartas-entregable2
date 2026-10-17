"""RoomSetupComponent: crea salas y valida la configuración contra el esquema del plug-in."""
from __future__ import annotations

from typing import Any, Mapping, Protocol

from juegocartas.nucleo.contrato import VariantePlugin


class IResolverVariante(Protocol):
    def resolver(self, codigo: str) -> VariantePlugin: ...


class ConfiguracionInvalida(ValueError):
    pass


class RoomSetup:
    def __init__(self, registro: IResolverVariante) -> None:
        self._registro = registro

    def validar(self, variante: str, config: Mapping[str, Any]) -> dict[str, Any]:
        """Completa los valores por defecto y rechaza claves o tipos que el plug-in no declara."""
        esquema = self._registro.resolver(variante).esquema_configuracion()
        desconocidas = set(config) - set(esquema)
        if desconocidas:
            raise ConfiguracionInvalida(f"Parámetros no soportados por {variante}: {sorted(desconocidas)}")
        final = {clave: spec["defecto"] for clave, spec in esquema.items()}
        for clave, valor in config.items():
            if not isinstance(valor, esquema[clave]["tipo"]):
                raise ConfiguracionInvalida(f"{clave} debe ser {esquema[clave]['tipo'].__name__}")
            final[clave] = valor
        return final
