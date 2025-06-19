#!/usr/bin/env python3
"""
Módulo: rep-export-Windows_generate_structure.py
Ubicación: rep-export-Windows/

Genera una estructura ASCII filtrada del repo, ahora respetando `.gitignore`
y forzando la exportación de `.gitignore` y `estructura.txt`.
"""

import os
import sys
import argparse
import logging
import tempfile
from pathlib import Path
import fnmatch
from pathspec import PathSpec
from cli_utils import load_ignore_spec, is_ignored


# Listas de exclusión por defecto
IGNORED_DIRS = {
    '.git', '.svn', '.hg', '.idea', '__pycache__', 'node_modules',
    'dist', 'build', 'venv', '.mypy_cache'
}
IGNORED_FILES = {'.DS_Store'}
IGNORED_EXT = {
    '.pyc', '.class', '.o', '.exe', '.dll', '.so', '.dylib', '.pdb'
}


def load_gitignore_patterns(repo_root: Path) -> PathSpec:
    """
    Carga el .gitignore y compila sus patrones con pathspec.
    """
    gitignore = repo_root / ".gitignore"
    if gitignore.is_file():
        lines = [
            line.strip() for line in gitignore.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith('#')
        ]
        return PathSpec.from_lines("gitwildmatch", lines)
    # Spec vacío
    return PathSpec.from_lines("gitwildmatch", [])


def matches_gitignore(path: Path, repo_root: Path, spec: PathSpec) -> bool:
    """
    Devuelve True si la ruta relativa coincide con alguna regla de .gitignore.
    """
    rel = str(path.relative_to(repo_root))
    return spec.match_file(rel)


def should_skip(path: Path,
                repo_root: Path,
                exclude_patterns,
                honor_gitignore: bool,
                gitignore_spec: PathSpec) -> bool:
    """
    Determina si un path debe omitirse según:
    - reglas estáticas (IGNORED_DIRS, IGNORED_FILES, IGNORED_EXT)
    - patrones de exclusión por usuario (--exclude, --exclude-from)
    - reglas de .gitignore (si honor_gitignore es True)
    Excepciones: siempre incluir `.gitignore` y `estructura.txt`.
    """
    name = path.name
    rel = str(path.relative_to(repo_root))

    # 1) Exclusiones fijas
    if name in IGNORED_DIRS or name in IGNORED_FILES:
        return True
    if path.suffix.lower() in IGNORED_EXT:
        return True
    # Archivos ocultos (excepto .gitignore y estructura.txt)
    if name.startswith('.') and rel not in ('.gitignore', 'estructura.txt'):
        return True

    # 2) Exclusión .gitignore
    if honor_gitignore and gitignore_spec:
        if matches_gitignore(path, repo_root, gitignore_spec):
            # Forzar inclusión de estos dos archivos
            if rel in ('.gitignore', 'estructura.txt'):
                return False
            return True

    # 3) Exclusión adicional por CLI
    if exclude_patterns:
        for pat in exclude_patterns:
            if fnmatch.fnmatch(rel, pat):
                return True

    return False


def ascii_tree(root: Path,
               repo_root: Path,
               prefix: str = '',
               args=None,
               gitignore_spec: PathSpec = None) -> list:
    """
    Genera líneas de un árbol ASCII, omitiendo paths según should_skip().
    """
    lines = []
    try:
        entries = sorted(root.iterdir(), key=lambda p: p.name.lower())
    except PermissionError:
        logging.warning(f"Permiso denegado: {root}")
        return lines

    entries = [
        e for e in entries
        if not should_skip(e, repo_root, args.exclude, args.honor_gitignore, gitignore_spec)
    ]

    for idx, entry in enumerate(entries):
        connector = '└── ' if idx == len(entries) - 1 else '├── '
        lines.append(f"{prefix}{connector}{entry.name}")
        if entry.is_dir() and not entry.is_symlink():
            extension = '    ' if idx == len(entries) - 1 else '│   '
            lines += ascii_tree(entry, repo_root, prefix + extension, args, gitignore_spec)

    return lines


def write_atomic(path: Path, lines: list):
    """
    Escribe las líneas en `path` de forma atómica.
    """
    tmp = tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8')
    with tmp:
        tmp.write('\n'.join(lines))
    Path(tmp.name).replace(path)
    logging.info(f"Estructura escrita en {path}")


def parse_args():
    p = argparse.ArgumentParser(description="Genera estructura ASCII filtrada del repo.")
    p.add_argument('--output', '-o', type=Path, default=Path('estructura.txt'),
                   help="Ruta de salida relativa al root del repositorio.")
    p.add_argument('--exclude', '-e', action='append', default=[],
                   help="Patrón glob para excluir (puede repetirse).")
    p.add_argument('--exclude-from', type=Path,
                   help="Archivo con patrones glob de exclusión (uno por línea).")
    p.add_argument('--honor-gitignore', action='store_true',
                   help="Excluir archivos/carpetas según .gitignore.")
    p.add_argument('--verbose', '-v', action='count', default=0,
                   help="Aumenta nivel de detalle en logs.")
    return p.parse_args()


def main():
    args = parse_args()
    level = logging.WARNING - (10 * args.verbose)
    logging.basicConfig(level=level, format='[%(levelname)s] %(message)s')

    repo_root = Path(__file__).resolve().parent
    os.chdir(repo_root)

    # Cargar .gitignore si corresponde
    gitignore_spec = load_gitignore_patterns(repo_root) if args.honor_gitignore else None

    # Cargar exclusiones desde archivo
    if args.exclude_from and args.exclude_from.is_file():
        with args.exclude_from.open(encoding='utf-8') as f:
            lines = [ln.strip() for ln in f if ln.strip() and not ln.startswith('#')]
            args.exclude.extend(lines)

    logging.info(f"Generando estructura desde {repo_root}")
    lines = ascii_tree(repo_root, repo_root, prefix='', args=args, gitignore_spec=gitignore_spec)

    output_path = repo_root / args.output
    write_atomic(output_path, lines)


if __name__ == '__main__':
    main()
