#!/usr/bin/env python3
"""
Script: generate_structure.py
Plataformas objetivo: Linux y macOS

Este script genera un archivo `estructura.txt` que muestra el árbol completo
filtrado del repositorio usando solo caracteres ASCII y codificado en UTF-8.
Admite exclusiones sensibles y respetar .gitignore, así como ejecución en "dry-run".

Uso:
  python3 generate_structure.py [--root PATH] [--output PATH]
                               [--honor-gitignore]
                               [-e PATTERN ...] [--exclude-from FILE]
                               [--dry-run] [-v]

Ejemplo:
  python3 generate_structure.py --honor-gitignore -e node_modules -e '*.log' --dry-run
"""
import os
import sys
import argparse
import logging
import tempfile
from pathlib import Path
import fnmatch

# Exclusiones por defecto
IGNORED_DIRS = {
    '.git', '.svn', '.hg', '.idea', '__pycache__', 'node_modules',
    'dist', 'build', 'venv', '.mypy_cache'
}
IGNORED_FILES = {'.DS_Store'}
IGNORED_EXT = {
    '.pyc', '.class', '.o', '.exe', '.dll', '.so', '.dylib', '.pdb'
}


def load_gitignore_patterns(repo_root: Path):
    """Carga patrones desde .gitignore"""
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
    # Ocultos (excepto .gitignore)
    if name.startswith('.') and name != '.gitignore':
        return True
    # Patrones extra
    if exclude_patterns and matches_pattern(path, exclude_patterns, repo_root):
        return True
    # Patrones de .gitignore
    if honor_gitignore and gitignore_patterns and matches_pattern(path, gitignore_patterns, repo_root):
        # Excepciones: siempre incluir .gitignore y estructura.txt
        rel = str(path.relative_to(repo_root))
        if rel in ('.gitignore', 'estructura.txt'):
            return False
        return True
    return False


def ascii_tree(root: Path, repo_root: Path, prefix='', args=None, gitignore_patterns=None):
    """Construye lista de líneas con árbol ASCII filtrado"""
    lines = []
    try:
        entries = sorted(root.iterdir(), key=lambda p: p.name.lower())
    except PermissionError:
        logging.warning(f"Permiso denegado: {root}")
        return lines

    entries = [
        e for e in entries
        if not should_skip(e, repo_root, args.exclude, args.honor_gitignore, gitignore_patterns)
    ]

    for idx, entry in enumerate(entries):
        connector = '└── ' if idx == len(entries) - 1 else '├── '
        lines.append(f"{prefix}{connector}{entry.name}")
        if entry.is_dir() and not entry.is_symlink():
            extension = '    ' if idx == len(entries) - 1 else '│   '
            lines += ascii_tree(entry, repo_root, prefix + extension, args, gitignore_patterns)

    return lines


def write_atomic(path: Path, lines):
    """Escribe de forma atómica reemplazando el archivo destino."""
    # Crear temporal en la misma carpeta para evitar cross-device errors
    tmp = tempfile.NamedTemporaryFile(
        'w',
        delete=False,
        encoding='utf-8',
        dir=path.parent
    )
    with tmp:
        tmp.write('\n'.join(lines))
    tmp_path = Path(tmp.name)
    tmp_path.replace(path)
    logging.info(f"Estructura escrita en {path}")


def parse_args():
    p = argparse.ArgumentParser(
        description="Genera un árbol ASCII del proyecto con exclusiones de privacidad."
    )
    p.add_argument(
        '--root', type=Path,
        help="Ruta raíz del proyecto (por defecto: repo root)"
    )
    p.add_argument(
        '--output', '-o', type=Path, default=Path('estructura.txt'),
        help="Archivo de destino (por defecto: <root>/estructura.txt)"
    )
    p.add_argument(
        '--honor-gitignore', action='store_true',
        help="Excluir patrones listados en .gitignore"
    )
    p.add_argument(
        '-e', '--exclude', action='append', default=[],
        help="Patrón glob adicional a excluir (repetible)"
    )
    p.add_argument(
        '--exclude-from', type=Path,
        help="Archivo con patrones glob a excluir (uno por línea)"
    )
    p.add_argument(
        '--dry-run', action='store_true',
        help="Imprime árbol sin escribir archivo"
    )
    p.add_argument(
        '-v', '--verbose', action='count', default=0,
        help="Aumenta nivel de detalle en logs"
    )
    return p.parse_args()


def main():
    args = parse_args()
    level = logging.WARNING - (10 * args.verbose)
    logging.basicConfig(level=level, format='[%(levelname)s] %(message)s')

    repo_root = args.root or Path(__file__).resolve().parents[1]
    os.chdir(repo_root)

    gitignore_patterns = (
        load_gitignore_patterns(repo_root)
        if args.honor_gitignore else []
    )

    if args.exclude_from and args.exclude_from.is_file():
        extra = [
            line.strip() for line in
            args.exclude_from.read_text(encoding='utf-8').splitlines()
            if line.strip() and not line.startswith('#')
        ]
        args.exclude.extend(extra)

    logging.info(f"Generando estructura desde {repo_root}")
    lines = ascii_tree(
        repo_root, repo_root, prefix='',
        args=args, gitignore_patterns=gitignore_patterns
    )

    if args.dry_run:
        print('\n'.join(lines))
        logging.info("[dry-run] no se escribió archivo")
        return

    output_path = args.output if args.output.is_absolute() else repo_root / args.output
    write_atomic(output_path, lines)
    print(f"\n📂 Estructura exportada a: {output_path}")


if __name__ == '__main__':
    main()
