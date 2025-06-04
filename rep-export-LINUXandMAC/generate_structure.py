#!/usr/bin/env python3
"""
📦 Script: generate_structure.py
🖥️ Plataformas objetivo: Linux y macOS

Descripción general
===================
Este script genera un archivo `estructura.txt` que muestra el árbol completo
de carpetas y archivos del repositorio usando solo caracteres ASCII y
codificado en UTF‑8. El archivo se coloca por defecto en la raíz del proyecto,
aunque se puede cambiar con la opción `--output`.

¿Por qué necesitamos esto?
-------------------------
1. **Documentación viva del código**: Al hacer *commits* frecuentes del árbol
   textual es fácil detectar cambios estructurales en revisiones de código.
2. **Consistencia cross‑platform**: La salida ASCII es estable entre entornos,
   lo que evita sorpresas en CI/CD al comparar *diffs*.
3. **Compatibilidad con TiddlyWiki**: Otros scripts del proyecto consumen
   `estructura.txt` para generar *tiddlers*.

Dependencias
------------
* `tree`   → Instálalo con `sudo apt install tree` (Debian/Ubuntu),
              `brew install tree` (macOS), o el gestor de paquetes de tu distro.
* Python ≥ 3.8 (para `pathlib` y `argparse` con `subparsers` ordenados).

Modos de ejecución (“runners”)
-----------------------------
El script admite **tres runners** que cubren los casos de uso más habituales:

1. **Runner CLI interactivo**
   Ejecuta:
   ```bash
   python3 rep-export-LINUXandMAC/generate_structure.py
   ```
   Crea/actualiza `estructura.txt` en la raíz y muestra un resumen ✅.

2. **Runner CLI ‘dry‑run’**
   Ejecuta:
   ```bash
   python3 rep-export-LINUXandMAC/generate_structure.py --dry-run
   ```
   Imprime la salida de `tree` en pantalla sin escribir el archivo.
   Útil para inspecciones rápidas y para evitar *commits* de prueba.

3. **Runner de librería (importable)**
   Permite que otros módulos llamen:
   ```python
   from rep_export_linuxandmac.generate_structure import generate_structure
   generate_structure(root=Path.cwd(), output=Path("/tmp/mi_tree.txt"))
   ```
   Ideal para pipelines CI/CD o para integrarlo en scripts más grandes.

Estos tres runners son buenos porque:
* **Flexibilidad** → Puedes usarlo de forma manual, automatizada o embebida.
* **Reutilización** → No duplicas lógica; la misma función se comparte.
* **Seguridad** → `--dry-run` evita sobreescrituras accidentales.

Uso detallado
-------------
```bash
$ python3 generate_structure.py [-h] [--root PATH] [--output PATH] [--extra-args "-I node_modules"] [--dry-run]
```
* `--root PATH`     Ruta al proyecto (por defecto, dos niveles arriba del script).
* `--output PATH`   Archivo de salida (por defecto, `<root>/estructura.txt`).
* `--extra-args`    Flags adicionales que se pasarán literalmente a `tree`.
* `--dry-run`       Muestra la salida por STDOUT en lugar de escribir archivo.

Códigos de salida
-----------------
* `0` → Ejecución satisfactoria.
* `1` → Error de dependencia (`tree` ausente).
* `2` → Error al ejecutar `tree` o escribir el archivo.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Final

DEFAULT_ENCODING: Final = "utf-8"


def _run_tree(root: Path, extra_args: str | None) -> str:
    """Ejecuta el comando `tree` y devuelve su salida como *str* UTF‑8.

    Parameters
    ----------
    root        Ruta desde donde se listarán los archivos.
    extra_args  Cadena con opciones adicionales a `tree` (p.ej. "-I *.pyc").
    """
    if shutil.which("tree") is None:
        msg = (
            "❌ No se encontró el comando `tree`. "
            "Instálalo con `sudo apt install tree` o `brew install tree`."
        )
        print(msg, file=sys.stderr)
        sys.exit(1)

    # Construimos la lista de argumentos para subprocess
    cmd = ["tree", "-a", "-F"]  # -a → incluye ocultos | -F → sufijo por tipo
    if extra_args:
        cmd.extend(extra_args.split())

    try:
        completed = subprocess.run(
            cmd,
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        print("❌ Error al ejecutar `tree`:", exc.stderr.decode(DEFAULT_ENCODING), file=sys.stderr)
        sys.exit(2)

    return completed.stdout.decode(DEFAULT_ENCODING, errors="replace")


def generate_structure(*, root: Path | None = None, output: Path | None = None, extra_args: str | None = None, dry_run: bool = False) -> None:
    """Genera el archivo `estructura.txt` o imprime la salida si *dry_run*.

    Parameters
    ----------
    root        Directorio raíz a escanear (defaults to repo root).
    output      Ruta completa al archivo de salida.
    extra_args  Flags extra para el comando `tree`.
    dry_run     Cuando es `True`, no se escribe en disco; se imprime por STDOUT.
    """
    root = root or Path(__file__).resolve().parents[1]
    output = output or root / "estructura.txt"

    tree_output = _run_tree(root, extra_args)

    if dry_run:
        print(tree_output)
        print("\n[dry-run] No se escribió archivo.")
        return

    try:
        output.write_text(tree_output, encoding=DEFAULT_ENCODING)
    except OSError as exc:
        print(f"❌ No se pudo escribir {output}: {exc}", file=sys.stderr)
        sys.exit(2)

    print("\n📂 Estructura del proyecto exportada a:\n   ", output)


def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Genera un árbol ASCII del proyecto.")
    parser.add_argument("--root", type=Path, help="Ruta raíz del proyecto (por defecto: repo root)")
    parser.add_argument("--output", type=Path, help="Archivo de destino (por defecto: <root>/estructura.txt)")
    parser.add_argument("--extra-args", help="Argumentos adicionales para el comando `tree`.")
    parser.add_argument("--dry-run", action="store_true", help="Imprime la salida sin crear archivo.")
    return parser


if __name__ == "__main__":
    args = _build_argparser().parse_args()
    generate_structure(
        root=args.root,
        output=args.output,
        extra_args=args.extra_args,
        dry_run=args.dry_run,
    )
