"""R4. Ausencia de dependencias cíclicas (ADP, Richards y Ford, 2025, cap. 3 y 6).

PyTestArch no trae una regla de ciclos, así que el grafo de imports se arma con `ast`
(biblioteca estándar) a nivel de componente y se busca un ciclo con DFS.
"""
import ast
from pathlib import Path

from conftest import SRC

PAQUETE = SRC / "juegocartas"


def componente(modulo: str) -> str:
    """juegocartas.nucleo.turno.orquestador -> nucleo.turno ; juegocartas.plugins.clasica.plugin -> plugins.clasica"""
    partes = modulo.split(".")[1:]
    return ".".join(partes[:2]) if partes[0] in ("nucleo", "plugins") else partes[0]


def grafo_componentes(paquete: Path = PAQUETE) -> dict[str, set[str]]:
    grafo: dict[str, set[str]] = {}
    for archivo in paquete.rglob("*.py"):
        relativo = archivo.relative_to(paquete.parent).with_suffix("")
        modulo = ".".join(relativo.parts).removesuffix(".__init__")
        if modulo.count(".") < 2 and not modulo.endswith(("presentacion", "persistencia")):
            continue  # __init__ de juegocartas, nucleo o plugins: no son componentes
        origen = componente(modulo)
        destinos = grafo.setdefault(origen, set())
        for nodo in ast.walk(ast.parse(archivo.read_text(encoding="utf-8"))):
            if isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.module.startswith("juegocartas."):
                destinos.add(componente(nodo.module))
            elif isinstance(nodo, ast.Import):
                destinos |= {componente(a.name) for a in nodo.names if a.name.startswith("juegocartas.")}
        destinos.discard(origen)
    return grafo


def buscar_ciclo(grafo: dict[str, set[str]]) -> list[str] | None:
    estado: dict[str, int] = {}  # 1 = en la pila, 2 = terminado
    pila: list[str] = []

    def visitar(nodo: str) -> list[str] | None:
        estado[nodo] = 1
        pila.append(nodo)
        for vecino in sorted(grafo.get(nodo, ())):
            if estado.get(vecino) == 1:
                return pila[pila.index(vecino):] + [vecino]
            if vecino not in estado and (ciclo := visitar(vecino)):
                return ciclo
        pila.pop()
        estado[nodo] = 2
        return None

    for nodo in sorted(grafo):
        if nodo not in estado and (ciclo := visitar(nodo)):
            return ciclo
    return None


def test_grafo_de_componentes_es_aciclico():
    ciclo = buscar_ciclo(grafo_componentes())
    assert ciclo is None, "Dependencia cíclica entre componentes: " + " -> ".join(ciclo)


def test_el_detector_encuentra_ciclos():
    """Prueba de la prueba: un grafo con ciclo debe ser detectado."""
    assert buscar_ciclo({"a": {"b"}, "b": {"c"}, "c": {"a"}}) == ["a", "b", "c", "a"]
