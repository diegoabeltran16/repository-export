#!/usr/bin/env python3
import os
import sys
import argparse
import logging
import tempfile
from pathlib import Path
import fnmatch

# Listas de exclusión por defecto
IGNORED_DIRS = {
    '.git', '.svn', '.hg', '.idea', '__pycache__', 'node_modules',
    'dist', 'build', 'venv', '.mypy_cache'
}
IGNORED_FILES = {'.DS_Store'}
IGNORED_EXT = {
    '.pyc', '.class', '.o', '.exe', '.dll', '.so', '.dylib', '.pdb'
}

def load_gitignore_patterns(repo_root: Path):
    patterns = []
    gitignore = repo_root / '.gitignore'
    if gitignore.is_file():
        for line in gitignore.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            patterns.append(line)
    return patterns


def matches_pattern(path: Path, patterns, repo_root: Path):
    rel = str(path.relative_to(repo_root))
    return any(fnmatch.fnmatch(rel, pat) for pat in patterns)

def should_skip(path: Path, repo_root: Path, exclude_patterns, honor_gitignore, gitignore_patterns):
    name = path.name
    if name in IGNORED_DIRS or name in IGNORED_FILES:
        return True
    if path.suffix.lower() in IGNORED_EXT:
        return True
    if name.startswith('.'):
        return True
    if exclude_patterns and matches_pattern(path, exclude_patterns, repo_root):
        return True
    if honor_gitignore and gitignore_patterns and matches_pattern(path, gitignore_patterns, repo_root):
        return True
    return False

def ascii_tree(root: Path, repo_root: Path, prefix='', args=None, gitignore_patterns=None):
    lines = []
    try:
        entries = sorted(root.iterdir(), key=lambda p: p.name.lower())
    except PermissionError:
        logging.warning(f"Permiso denegado: {root}")
        return lines
    entries = [e for e in entries if not should_skip(e, repo_root, args.exclude, args.honor_gitignore, gitignore_patterns)]
    for idx, entry in enumerate(entries):
        connector = '└── ' if idx == len(entries) - 1 else '├── '
        lines.append(f"{prefix}{connector}{entry.name}")
        if entry.is_dir() and not entry.is_symlink():
            extension = '    ' if idx == len(entries) - 1 else '│   '
            lines += ascii_tree(entry, repo_root, prefix + extension, args, gitignore_patterns)
    return lines

def write_atomic(path: Path, lines):
    tmp = tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8')
    with tmp:
        tmp.write('\n'.join(lines))
    tmp_path = Path(tmp.name)
    tmp_path.replace(path)
    logging.info(f"Estructura escrita en {path}")

def parse_args():
    p = argparse.ArgumentParser(description="Genera estructura ASCII filtrada del repo.")
    p.add_argument('--output', '-o', type=Path, default=Path('estructura.txt'),
                   help="Ruta de salida relative al root del repositorio.")
    p.add_argument('--exclude', '-e', action='append', default=[],
                   help="Patrón glob para excluir (puede repetirse).")
    p.add_argument('--exclude-from', type=Path,
                   help="Archivo con patrones glob de exclusión (uno por línea).")
    p.add_argument('--honor-gitignore', action='store_true',
                   help="Excluir archivos/carpetas según .gitignore.")
    p.add_argument('--verbose', '-v', action='count', default=0,
                   help="Aumenta el nivel de verbosidad (más -v más logs).")
    return p.parse_args()

def main():
    args = parse_args()
    # Ajuste de logging
    level = logging.WARNING - (10 * args.verbose)
    logging.basicConfig(level=level, format='[%(levelname)s] %(message)s')
    # Determinar repo root
    repo_root = Path(__file__).resolve().parent.parent
    os.chdir(repo_root)
    # Cargar patrones de .gitignore
    gitignore_patterns = load_gitignore_patterns(repo_root) if args.honor_gitignore else []
    # Cargar exclude-from si se indicó
    if args.exclude_from and args.exclude_from.is_file():
        args.exclude += [line.strip() for line in args.exclude_from.read_text(encoding='utf-8').splitlines()
                          if line.strip() and not line.startswith('#')]
    # Generar árbol
    logging.info(f"Generando estructura desde {repo_root}")
    lines = ascii_tree(repo_root, repo_root, prefix='', args=args, gitignore_patterns=gitignore_patterns)
    # Escribir
    output_path = repo_root / args.output
    write_atomic(output_path, lines)

if __name__ == '__main__':
    main()
