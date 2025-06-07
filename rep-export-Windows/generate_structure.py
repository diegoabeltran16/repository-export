"""
#!/usr/bin/env python3
Rep-Export: Generador de estructura de proyecto (Windows)
Crea un árbol ASCII filtrado de archivos/carpetas del repositorio,
excluyendo dot-files, dependencias, artefactos y Gitignored si se indica.
Escritura atómica y sin llamadas a shell.
"""
import os
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


def matches_pattern(path: Path, patterns, repo_root: Path) -> bool:
    rel = str(path.relative_to(repo_root))
    return any(fnmatch.fnmatch(rel, pat) for pat in patterns)

def should_skip(path: Path, repo_root: Path, exclude_patterns, honor_gitignore, gitignore_patterns) -> bool:
    name = path.name
    # Excluir directorios, archivos y extensiones no deseadas
    if name in IGNORED_DIRS or name in IGNORED_FILES:
        return True
    if path.suffix.lower() in IGNORED_EXT:
        return True
    if name.startswith('.'):
        return True
    # Excluir patrones personalizados
    if exclude_patterns and matches_pattern(path, exclude_patterns, repo_root):
        return True
    # Excluir según .gitignore
    if honor_gitignore and gitignore_patterns and matches_pattern(path, gitignore_patterns, repo_root):
        return True
    return False


def ascii_tree(root: Path, repo_root: Path, prefix: str = '', args=None, gitignore_patterns=None) -> list:
    lines = []
    try:
        entries = sorted(root.iterdir(), key=lambda p: p.name.lower())
    except PermissionError:
        logging.warning(f"Permiso denegado: {root}")
        return lines
    # Filtrar
    filtered = [e for e in entries if not should_skip(e, repo_root, args.exclude, args.honor_gitignore, gitignore_patterns)]
    for idx, entry in enumerate(filtered):
        connector = '└── ' if idx == len(filtered) - 1 else '├── '
        lines.append(f"{prefix}{connector}{entry.name}")
        # Recursión para directorios
        if entry.is_dir() and not entry.is_symlink():
            extension = '    ' if idx == len(filtered) - 1 else '│   '
            lines.extend(ascii_tree(entry, repo_root, prefix + extension, args, gitignore_patterns))
    return lines


def write_atomic(path: Path, lines: list) -> None:
    # Escritura atómica: temp -> replace
    tmp = tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8')
    with tmp:
        tmp.write('\n'.join(lines))
    tmp_path = Path(tmp.name)
    # Reemplazo atómico
    tmp_path.replace(path)
    # Ajustar permisos en Unix
    try:
        path.chmod(0o600)
    except Exception:
        pass
    logging.info(f"Estructura escrita en {path}")


def parse_args():
    parser = argparse.ArgumentParser(description="Genera estructura ASCII filtrada del repo.")
    parser.add_argument('--output', '-o', type=Path, default=Path('estructura.txt'),
                        help="Archivo de salida relativo al root.")
    parser.add_argument('--exclude', '-e', action='append', default=[],
                        help="Patrón glob para excluir rutas.")
    parser.add_argument('--exclude-from', type=Path,
                        help="Archivo con patrones glob a excluir.")
    parser.add_argument('--honor-gitignore', action='store_true',
                        help="Excluir rutas según .gitignore.")
    parser.add_argument('--verbose', '-v', action='count', default=0,
                        help="Incrementa nivel de logging.")
    return parser.parse_args()


def main():
    args = parse_args()
    # Configurar logging
    level = max(logging.DEBUG, logging.WARNING - 10 * args.verbose)
    logging.basicConfig(level=level, format='[%(levelname)s] %(message)s')
    # Directorio raíz del repo
    repo_root = Path(__file__).resolve().parent.parent
    os.chdir(repo_root)
    # Cargar patrones de .gitignore
    gitignore_patterns = load_gitignore_patterns(repo_root) if args.honor_gitignore else []
    # Cargar patterns desde archivo si existe
    if args.exclude_from and args.exclude_from.is_file():
        args.exclude += [ln.strip() for ln in args.exclude_from.read_text(encoding='utf-8').splitlines()
                         if ln.strip() and not ln.startswith('#')]
    logging.info(f"Generando estructura desde {repo_root}")
    # Generar y escribir
    lines = ascii_tree(repo_root, repo_root, '', args, gitignore_patterns)
    write_atomic(repo_root / args.output, lines)

if __name__ == '__main__':
    main()
