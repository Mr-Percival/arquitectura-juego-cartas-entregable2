"""Publica el repositorio en un repo público nuevo y deja privado el anterior.

Uso (desde la raíz del repo):
    python herramientas/publicar_repo.py --nuevo arquitectura-juego-cartas-entregable2 \
        --anterior Mr-Percival/arquitectura-juego-cartas

Pasos (se puede volver a correr: cada paso revisa si ya está hecho):
  1. Crea el repo público con gh, si no existe.
  2. Sube main y espera a que el CI (fitness functions) termine en verde.
  3. Cambia el enlace del informe local (que no se versiona porque lleva cédulas) y regenera el PDF.
  4. Deja origin apuntando al repo nuevo y el anterior como remoto "anterior".
  5. Solo si todo lo anterior salió bien, vuelve privado el repo anterior.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
INFORME = RAIZ / "docs" / "informe" / "Entregable2.html"


def run(*cmd: str, check: bool = True, capturar: bool = True) -> str:
    r = subprocess.run(cmd, cwd=RAIZ, text=True, capture_output=capturar, encoding="utf-8")
    if check and r.returncode != 0:
        sys.exit(f"Falló: {' '.join(cmd)}\n{r.stderr}")
    return (r.stdout or "").strip()


def paso(n: int, texto: str) -> None:
    print(f"\n[{n}/5] {texto}")


def crear_repo(completo: str) -> None:
    paso(1, f"Repo público {completo}")
    existe = subprocess.run(["gh", "repo", "view", completo], cwd=RAIZ, capture_output=True).returncode == 0
    if existe:
        print("  ya existe")
        return
    run("gh", "repo", "create", completo, "--public",
        "--description", "Entregable 2 · Fundamentos de Arquitectura de Software (UNAL): microkernel, ADRs y fitness functions")
    print("  creado")


def subir_y_esperar_ci(completo: str) -> None:
    paso(2, "Subir main y esperar el CI")
    url = f"https://github.com/{completo}.git"
    remotos = run("git", "remote").split()
    if "entrega" not in remotos:
        run("git", "remote", "add", "entrega", url)
    run("git", "push", "entrega", "main")
    sha = run("git", "rev-parse", "HEAD")
    for _ in range(30):  # el workflow tarda unos segundos en aparecer
        corridas = json.loads(run("gh", "run", "list", "-R", completo, "-L", "5", "--json", "databaseId,headSha"))
        ids = [c["databaseId"] for c in corridas if c["headSha"] == sha]
        if ids:
            break
        time.sleep(5)
    else:
        sys.exit("  El CI no arrancó. Revisa la pestaña Actions del repo nuevo.")
    r = subprocess.run(["gh", "run", "watch", str(ids[0]), "-R", completo, "--exit-status"],
                       cwd=RAIZ, capture_output=True)
    if r.returncode != 0:
        sys.exit("  El CI falló: no se toca nada más. Revisa la pestaña Actions del repo nuevo.")
    print("  CI en verde")


def actualizar_informe(anterior: str, completo: str) -> None:
    paso(3, "Enlace del informe y PDF")
    if not INFORME.exists():
        print("  no hay informe local; se omite")
        return
    texto = INFORME.read_text(encoding="utf-8")
    nuevo = texto.replace(f"https://github.com/{anterior}\"", f"https://github.com/{completo}\"") \
                 .replace(f"https://github.com/{anterior}<", f"https://github.com/{completo}<")
    if nuevo != texto:
        INFORME.write_text(nuevo, encoding="utf-8", newline="")
        print("  enlace actualizado")
    else:
        print("  el enlace ya estaba actualizado")
    # build_pdf.py necesita PyMuPDF, que está en el Python del sistema y no en el venv
    r = subprocess.run(["python", "build_pdf.py"], cwd=INFORME.parent, text=True, capture_output=True)
    if r.returncode != 0:
        sys.exit(f"  No se pudo regenerar el PDF:\n{r.stderr}")
    print("  " + next((l for l in r.stdout.splitlines() if l.startswith("Entregable2.pdf")), "PDF regenerado"))


def reordenar_remotos(anterior: str) -> None:
    paso(4, "Remotos: origin → repo nuevo")
    remotos = run("git", "remote").split()
    if "entrega" not in remotos:
        print("  ya estaban reordenados")
        return
    if "origin" in remotos:
        run("git", "remote", "rename", "origin", "anterior")
    run("git", "remote", "rename", "entrega", "origin")
    run("git", "branch", "--set-upstream-to=origin/main", "main", check=False)
    print("  origin = repo nuevo; anterior = " + anterior)


def privatizar(anterior: str) -> None:
    paso(5, f"Volver privado {anterior}")
    vis = json.loads(run("gh", "repo", "view", anterior, "--json", "visibility"))["visibility"]
    if vis == "PRIVATE":
        print("  ya era privado")
        return
    run("gh", "repo", "edit", anterior, "--visibility", "private", "--accept-visibility-change-consequences")
    print("  ahora es privado")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nuevo", required=True, help="nombre del repo nuevo (sin dueño)")
    ap.add_argument("--anterior", required=True, help="dueño/nombre del repo que pasa a privado")
    a = ap.parse_args()
    dueno = run("gh", "api", "user", "-q", ".login")
    completo = f"{dueno}/{a.nuevo}"
    crear_repo(completo)
    subir_y_esperar_ci(completo)
    actualizar_informe(a.anterior, completo)
    reordenar_remotos(a.anterior)
    privatizar(a.anterior)
    print(f"\nListo. Repo del trabajo: https://github.com/{completo}")


if __name__ == "__main__":
    main()
