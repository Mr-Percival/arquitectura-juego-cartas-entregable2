"""Genera el diagrama E-R en notación de Barker (Oracle CASE) como fuente Graphviz dentro de un .puml.

Convenciones de Barker:
- Entidad: caja de esquinas redondeadas, nombre en mayúsculas.
- Atributos: '#' identificador único, '*' obligatorio, 'o' opcional.
- Cada relación tiene dos mitades. La mitad junto a una entidad es sólida si esa entidad DEBE
  participar ("must be") y punteada si PUEDE participar ("may be").
- Pata de gallo en el extremo "muchos". Barra perpendicular (UID bar) cuando la relación
  forma parte del identificador único de la entidad hija.

Uso: python generar_er_barker.py  ->  docs/modelos/er/er_barker.puml
"""
from pathlib import Path

SALIDA = Path(__file__).resolve().parents[1] / "docs" / "modelos" / "er" / "er_barker.puml"

ENTIDADES = {
    "JUGADOR": ["# id", "* alias", "o correo", "* creado en"],
    "SESIÓN": ["# id", "* token hash", "* estado", "* iniciada en", "* última actividad", "* expira en"],
    "SALA": ["# id", "* código invitación", "* capacidad", "* estado", "* creada en"],
    "VARIANTE": ["# código", "* nombre", "* versión plug-in", "* versión contrato", "* activa", "* registrada en"],
    "PARTIDA": ["# id", "* estado", "o iniciada en", "o finalizada en"],
    "PARÁMETRO PARTIDA": ["# clave", "* valor"],
    "PARTICIPACIÓN": ["* asiento", "* estado jugador"],
    "PUNTAJE ACUMULADO": ["* total", "* versión", "* actualizado en"],
    "RONDA": ["# id", "* número", "* estado", "* semilla", "* iniciada en", "o cerrada en", "o tipo cierre"],
    "CARTA": ["# código", "o rango", "o pinta"],
    "MANO JUGADOR": ["# id"],
    "CARTA MANO": ["# mazo número"],
    "TURNO JUGADA": ["# id", "* número turno", "* acción", "o mazo número", "* resultado",
                     "o motivo rechazo", "* comando id", "* ocurrida en"],
    "PUNTAJE RONDA": ["* penalización", "* bonificación"],
}

# (padre, hijo, padre_obligatorio, hijo_obligatorio, hijo_muchos, identificadora, frase_padre, frase_hijo)
# Lectura: cada PADRE [debe|puede] <frase_padre> [uno o más|uno] HIJO; cada HIJO [debe|puede] <frase_hijo> un PADRE.
RELACIONES = [
    ("JUGADOR", "SESIÓN", False, True, True, False, "abrir", "pertenecer a"),
    ("JUGADOR", "SALA", False, True, True, False, "ser anfitrión de", "ser creada por"),
    ("SALA", "PARTIDA", False, True, True, False, "alojar", "jugarse en"),
    ("VARIANTE", "PARTIDA", False, True, True, False, "regir", "regirse por"),
    ("JUGADOR", "PARTIDA", False, False, True, False, "ganar", "ser ganada por"),
    ("PARTIDA", "PARÁMETRO PARTIDA", False, True, True, True, "configurarse con", "configurar"),
    ("PARTIDA", "PARTICIPACIÓN", True, True, True, True, "tener", "ser de"),
    ("JUGADOR", "PARTICIPACIÓN", False, True, True, True, "participar en", "ser de"),
    ("PARTICIPACIÓN", "PUNTAJE ACUMULADO", False, True, False, True, "llevar", "ser de"),
    ("PARTIDA", "RONDA", False, True, True, False, "dividirse en", "pertenecer a"),
    ("PARTICIPACIÓN", "RONDA", False, False, True, False, "cerrar", "ser cerrada por"),
    ("RONDA", "MANO JUGADOR", False, True, True, False, "repartir", "darse en"),
    ("JUGADOR", "MANO JUGADOR", False, True, True, False, "sostener", "ser de"),
    ("MANO JUGADOR", "CARTA MANO", False, True, True, True, "contener", "estar en"),
    ("CARTA", "CARTA MANO", False, True, True, True, "ubicarse como", "ser"),
    ("MANO JUGADOR", "TURNO JUGADA", False, True, True, False, "registrar", "hacerse con"),
    ("CARTA", "TURNO JUGADA", False, False, True, False, "moverse en", "mover"),
    ("RONDA", "PUNTAJE RONDA", False, True, True, True, "liquidarse en", "liquidar"),
    ("JUGADOR", "PUNTAJE RONDA", False, True, True, True, "recibir", "asignarse a"),
]


def nodo(nombre: str) -> str:
    import unicodedata
    plano = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    return plano.replace(" ", "_")


def etiqueta(nombre: str, atributos: list[str]) -> str:
    filas = "".join(f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="10">{a}</FONT></TD></TR>' for a in atributos)
    return (f'<<TABLE BORDER="0" CELLSPACING="0" CELLPADDING="1"><TR><TD><B>{nombre}</B></TD></TR>'
            f'{filas}</TABLE>>')


def generar() -> str:
    lineas = [
        "@startdot er_barker",
        "digraph ER {",
        '  graph [rankdir=TB, splines=true, nodesep=0.45, ranksep=0.35, fontname="Arial", pad=0.2];',
        '  node [shape=box, style="rounded,filled", fillcolor="#F7F9FC", color="#2F4A6D", fontname="Arial", fontsize=11, margin="0.12,0.06"];',
        '  edge [color="#2F4A6D", fontname="Arial", fontsize=9, fontcolor="#333333", arrowsize=0.9];',
    ]
    for nombre, atributos in ENTIDADES.items():
        lineas.append(f"  {nodo(nombre)} [label={etiqueta(nombre, atributos)}];")
    for i, (padre, hijo, p_obl, h_obl, muchos, ident, f_padre, f_hijo) in enumerate(RELACIONES):
        mid = f"r{i}"
        lineas.append(f'  {mid} [shape=point, width=0.01, height=0.01, label=""];')
        estilo_p = "solid" if p_obl else "dashed"
        estilo_h = "solid" if h_obl else "dashed"
        cabeza = ("crow" if muchos else "none") + ("tee" if ident else "")
        cabeza = cabeza.replace("nonetee", "tee")
        lineas.append(f'  {nodo(padre)} -> {mid} [dir=none, style={estilo_p}, label=" {f_padre}"];')
        lineas.append(f'  {mid} -> {nodo(hijo)} [arrowhead={cabeza}, style={estilo_h}, label=" {f_hijo}"];')
    lineas += ["}", "@enddot"]
    return "\n".join(lineas) + "\n"


if __name__ == "__main__":
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(generar(), encoding="utf-8")
    print(SALIDA)
