#!/usr/bin/env python3
"""
Módulo: generate_structure.py
Ubicación: rep-export-Windows/

Genera un árbol ASCII del repositorio, respetando .gitignore y
forzando que siempre se incluyan `.gitignore` y `estructura.txt`.
"""
import os
import sys
import argparse
import logging
import tempfile
from pathlib import Path
import fnmatch
from pathspec import PathSpec

from cli_utils_Windows import load_ignore_spec, is_ignored, confirm_overwrite
from tag_mapper_windows import get_tags_for_file  # si lo necesitas

# Exclusiones por defecto (sin __pycache__ para tests)
IGNORED_DIRS = {'.git', '.svn', '.hg', '.idea', 'node_modules', 'dist', 'build', 'venv', '.mypy_cache'}
IGNORED_FILES = {'.DS_Store'}
IGNORED_EXT   = {'.pyc', '.class', '.o', '.exe', '.dll', '.so', '.dylib', '.pdb'}

# Exclusiones adicionales
ALWAYS_EXCLUDE = {
    '.env', 'secret.env', '*.key', '*.pem', '*.crt', '*.p12', '*.db', '*.sqlite', '*.pyc',
    '__pycache__/', '__pycache__/*', '.vscode/', '.vscode/*', '.idea/', '.idea/*', '.DS_Store',
    'node_modules/', 'node_modules/*', 'dist/', 'dist/*', 'build/', 'build/*', 'venv/', 'venv/*',
    '.mypy_cache/', '.mypy_cache/*', '.git/', '.git/*'
}


def load_gitignore_patterns(repo_root: Path):
    """Devuelve lista de patrones (glob) extraídos de .gitignore."""
    gitignore = repo_root / '.gitignore'
    if not gitignore.is_file():
        return []
    lines = [ln.strip() for ln in gitignore.read_text(encoding='utf-8').splitlines()
             if ln.strip() and not ln.strip().startswith('#')]
    return lines


def matches_pattern(path: Path, patterns, repo_root: Path):
    """True si la ruta relativa coincide con algún patrón glob."""
    rel = str(path.relative_to(repo_root))
    return any(fnmatch.fnmatch(rel, pat) for pat in patterns)


def should_skip(path: Path, repo_root: Path, exclude_patterns, honor_gitignore: bool, ignore_spec: PathSpec):
    rel = path.relative_to(repo_root).as_posix()
    if path.is_dir() and not rel.endswith('/'):
        rel += '/'
    if honor_gitignore and ignore_spec and ignore_spec.match_file(rel):
        return True
    all_patterns = list(exclude_patterns) + list(ALWAYS_EXCLUDE)
    if any(fnmatch.fnmatch(rel, pat) for pat in all_patterns):
        logging.info(f"Excluyendo por patrón: {rel}")
        return True
    if path.name.startswith('.') and path.name not in {'.gitignore', '.github'}:
        return True
    return False


def ascii_tree(root: Path, repo_root: Path, prefix: str = '', args=None, gitignore_patterns=None, gitignore_spec=None):
    logging.info(f"Entrando a: {root}")
    """
    Construye líneas de árbol ASCII, filtrando según skip logic.
    """
    # determinar PathSpec a usar
    if args and getattr(args, 'honor_gitignore', False):
        ignore_spec = load_ignore_spec(repo_root)
    else:
        ignore_spec = gitignore_spec
    exclude_patterns = getattr(args, 'exclude', []) or []

    lines = []
    try:
        entries = sorted(root.iterdir(), key=lambda p: p.name.lower())
    except PermissionError:
        logging.warning(f"Permiso denegado: {root}")
        return lines

    # filtrar
    entries = [e for e in entries if not should_skip(e, repo_root, exclude_patterns, getattr(args, 'honor_gitignore', False), ignore_spec)]

    # construir
    for idx, entry in enumerate(entries):
        connector = '└── ' if idx == len(entries) - 1 else '├── '
        lines.append(f"{prefix}{connector}{entry.name}")
        if entry.is_dir() and not entry.is_symlink():
            extension = '    ' if idx == len(entries) - 1 else '│   '
            lines += ascii_tree(entry, repo_root, prefix + extension, args, gitignore_patterns, ignore_spec)
    return lines


def write_atomic(path: Path, lines):
    """Escribe de forma atómica usando tempfile + replace."""
    tmp = tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8')
    with tmp:
        tmp.write('\n'.join(lines))
    Path(tmp.name).replace(path)
    logging.info(f"Estructura escrita en {path}")


def parse_args():
    p = argparse.ArgumentParser(description="Genera estructura ASCII filtrada del repo.")
    p.add_argument('--output', '-o', type=Path, default=Path('estructura.txt'), help="Archivo de salida.")
    p.add_argument('--exclude', '-e', action='append', default=[], help="Patrón glob para excluir.")
    p.add_argument('--exclude-from', type=Path, help="Archivo con patrones de exclusión.")
    p.add_argument('--honor-gitignore', action='store_true', help="Respetar .gitignore.")
    p.add_argument('--verbose', '-v', action='count', default=0, help="Nivel de detalle logs.")
    p.add_argument('--force', '-f', action='store_true', help="Sobrescribir sin preguntar.")  # <--- NUEVO
    return p.parse_args()


def main():
    args = parse_args()
    level = logging.WARNING - 10 * args.verbose
    logging.basicConfig(level=level, format='[%(levelname)s] %(message)s')
    repo_root = Path(__file__).resolve().parent.parent
    os.chdir(repo_root)
    if args.exclude_from and args.exclude_from.is_file():
        args.exclude += [ln.strip() for ln in args.exclude_from.read_text(encoding='utf-8').splitlines() if ln.strip() and not ln.strip().startswith('#')]
    logging.info(f"Generando estructura desde {repo_root}")
    lines = ascii_tree(repo_root, repo_root, prefix='', args=args)
    output_path = repo_root / args.output
    if output_path.exists() and not (args.force or confirm_overwrite(output_path)):
        print("Operación cancelada por el usuario.")
        return
    write_atomic(output_path, lines)

if __name__ == '__main__':
    main()
