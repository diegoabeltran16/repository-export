#!/usr/bin/env python3
"""
Script: generate_structure.py
Plataformas objetivo: Linux y macOS

Genera un archivo `estructura.txt` con el árbol del repositorio usando `tree`, filtrando archivos/carpetas sensibles para mejorar la privacidad.
Uso:
  python3 generate_structure.py [--root PATH] [--output PATH] [--honor-gitignore] [--exclude PATTERN] [--exclude-from FILE] [--dry-run]

Ejemplo:
  python3 generate_structure.py --honor-gitignore -e node_modules -e '*.log' --dry-run
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Final, Optional, List, Set

DEFAULT_ENCODING: Final = "utf-8"

# Exclusiones por privacidad
IGNORED_DIRS: Set[str] = {
    '.git', '.svn', '.hg', '.idea', '__pycache__', 'node_modules',
    'dist', 'build', 'venv', '.mypy_cache'
}
IGNORED_FILES: Set[str] = {'.DS_Store'}
IGNORED_EXT: Set[str] = {'.pyc', '.class', '.o', '.exe', '.dll', '.so', '.dylib', '.pdb'}


def load_gitignore_patterns(repo_root: Path) -> Set[str]:
    patterns: Set[str] = set()
    gitignore = repo_root / '.gitignore'
    if gitignore.is_file():
        for line in gitignore.read_text(encoding=DEFAULT_ENCODING).splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            patterns.add(line)
    return patterns


def build_exclude_glob(args: argparse.Namespace, repo_root: Path) -> str:
    """
    Construye patrón glob para excluir en `tree -I` basándose en las exclusiones por defecto,
    .gitignore, exclude-from y exclude.
    """
    patterns: Set[str] = set()
    patterns.update(IGNORED_DIRS)
    patterns.update(IGNORED_FILES)
    patterns.update(f"*{ext}" for ext in IGNORED_EXT)
    if args.honor_gitignore:
        patterns.update(load_gitignore_patterns(repo_root))
    if args.exclude_from:
        ef = Path(args.exclude_from)
        if ef.is_file():
            for line in ef.read_text(encoding=DEFAULT_ENCODING).splitlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.add(line)
    if args.exclude:
        patterns.update(args.exclude)
    return '|'.join(sorted(patterns))


def _run_tree(root: Path, exclude_glob: Optional[str]) -> str:
    """
    Ejecuta `tree` y devuelve la salida como UTF-8.
    """
    if shutil.which('tree') is None:
        print("❌ No se encontró el comando `tree`. Instálalo con tu gestor de paquetes.", file=sys.stderr)
        sys.exit(1)

    cmd = ['tree', '-a', '-F']
    if exclude_glob:
        cmd.extend(['-I', exclude_glob])

    try:
        result = subprocess.run(
            cmd,
            cwd=str(root),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    except subprocess.CalledProcessError as exc:
        print(f"❌ Error al ejecutar `tree`: {exc.stderr}", file=sys.stderr)
        sys.exit(2)

    return result.stdout


def generate_structure(
    root: Optional[Path] = None,
    output: Optional[Path] = None,
    honor_gitignore: bool = False,
    exclude: Optional[List[str]] = None,
    exclude_from: Optional[Path] = None,
    dry_run: bool = False
) -> None:
    root = root or Path(__file__).resolve().parents[1]
    output = output or root / 'estructura.txt'
    exclude = exclude or []

    exclude_glob = build_exclude_glob(
        argparse.Namespace(
            honor_gitignore=honor_gitignore,
            exclude=exclude,
            exclude_from=exclude_from
        ),
        root
    )

    tree_output = _run_tree(root, exclude_glob)

    if dry_run:
        print(tree_output)
        print("\n[dry-run] No se escribió archivo.")
        return

    try:
        output.write_text(tree_output, encoding=DEFAULT_ENCODING)
    except OSError as exc:
        print(f"❌ No se pudo escribir {output}: {exc}", file=sys.stderr)
        sys.exit(2)

    print(f"\n📂 Estructura exportada a: {output}")


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Genera un árbol ASCII del proyecto con exclusiones de privacidad."
    )
    p.add_argument('--root', type=Path, help="Ruta raíz del proyecto (por defecto: repo root)")
    p.add_argument('--output', type=Path, help="Archivo de destino (por defecto: <root>/estructura.txt)")
    p.add_argument('--honor-gitignore', action='store_true', help="Excluir patrones listados en .gitignore")
    p.add_argument('-e', '--exclude', action='append', default=[], help="Patrón glob adicional a excluir (puede repetirse).")
    p.add_argument('--exclude-from', type=Path, help="Archivo con patrones glob a excluir (uno por línea).")
    p.add_argument('--dry-run', action='store_true', help="Imprime la salida sin escribir archivo.")
    return p


if __name__ == '__main__':
    args = _build_argparser().parse_args()
    generate_structure(
        root=args.root,
        output=args.output,
        honor_gitignore=args.honor_gitignore,
        exclude=args.exclude,
        exclude_from=args.exclude_from,
        dry_run=args.dry_run
    )
