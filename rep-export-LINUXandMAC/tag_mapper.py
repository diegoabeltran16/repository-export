#!/usr/bin/env python3
"""
📦 Módulo: tag_mapper.py — Linux/macOS alineado a Windows
🎯 Plataforma: Linux / macOS

Función:
- Asigna tags semánticos a cada archivo del repositorio.
- Orden de precedencia:
  1. Tags personalizados desde JSON en `tiddler_tag_doc/`.
  2. Tag derivado por extensión o nombre especial, con emoji ⚙️.
  3. Fallback `--- 🧬 Por Clasificar`.
- Además provee:
  - `load_ignore_spec(repo_root)` para interpretar `.gitignore`.
  - `detect_language(path)` para syntax highlighting.

Salida:
- `List[str]` con tags en sintaxis TiddlyWiki (`[[Tag]]`).
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any

# Intentar importar pathspec para .gitignore
try:
    import pathspec  # type: ignore
except ImportError:
    pathspec = None  # type: ignore

# ========================================
# Rutas y carga de JSON personalizados
# ========================================
TIDDLER_TAG_DIR = Path(__file__).resolve().parent / "tiddler_tag_doc"
title_to_tags: Dict[str, List[str]] = {}
if TIDDLER_TAG_DIR.is_dir():
    for json_file in sorted(TIDDLER_TAG_DIR.glob("*.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for item in data:
                    title = item.get("title", "").strip()
                    tags_str = item.get("tags", "").strip()
                    if title and tags_str:
                        title_to_tags[title] = tags_str.split()
        except Exception as e:
            print(f"⚠️ Error leyendo {json_file.name}: {e}")

# ========================================
# Mapeo extensión → Tag y nombres especiales
# ========================================
EXTENSION_TAG_MAP: Dict[str, str] = {
    # Code
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", ".go": "Go", ".rs": "Rust",
    ".java": "Java", ".c": "C", ".cpp": "C++", ".cc": "C++", ".hpp": "C++",
    ".rb": "Ruby", ".php": "PHP", ".kt": "Kotlin", ".swift": "Swift",
    # Scripting
    ".sh": "Shell", ".bash": "Shell", ".ps1": "PowerShell", ".bat": "Batch",
    # Markup / data
    ".md": "Markdown", ".rst": "Markdown", ".html": "HTML", ".css": "CSS",
    ".json": "JSON", ".yml": "YAML", ".yaml": "YAML", ".toml": "TOML",
    ".csv": "CSV", ".xml": "XML", ".sql": "SQL", ".txt": "Text"
}

SPECIAL_FILENAMES: Dict[str, str] = {
    "Dockerfile": "Dockerfile",
    "Makefile": "Makefile",
    "README": "README",
    "LICENSE": "License",
    ".gitignore": "Git"
}

DEFAULT_TAG = "--- 🧬 Por Clasificar"

# ========================================
# Función para interpretar .gitignore
# ========================================
def load_ignore_spec(repo_root: Path) -> Any:
    """
    Retorna un PathSpec para ignorar según .gitignore.
    Si pathspec no está disponible, no ignora nada.
    """
    if pathspec:
        gitignore = repo_root / '.gitignore'
        if gitignore.is_file():
            patterns = gitignore.read_text(encoding='utf-8').splitlines()
            return pathspec.PathSpec.from_lines('gitwildmatch', patterns)
    class DummySpec:
        def match_file(self, file_path: str) -> bool:
            return False
    return DummySpec()

# ========================================
# Mapeo para syntax highlighting
# ========================================
HIGHLIGHT_MAP: Dict[str, str] = {
    '.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.go': 'go', '.rs': 'rust',
    '.java': 'java', '.c': 'c', '.cpp': 'cpp', '.txt': 'text', '.md': 'markdown',
    '.json': 'json', '.html': 'html', '.css': 'css', '.yml': 'yaml', '.xml': 'xml'
}

SPECIAL_HIGHLIGHT: Dict[str, str] = {
    '.gitignore': 'gitignore', 'Dockerfile': 'dockerfile', 'Makefile': 'makefile',
    'README': 'markdown', 'LICENSE': 'text'
}

# ========================================
# Funciones principales
# ========================================

def detect_language(file_path: Path) -> str:
    """Devuelve la etiqueta de lenguaje para bloques Markdown."""
    name = file_path.name
    if name in SPECIAL_HIGHLIGHT:
        return SPECIAL_HIGHLIGHT[name]
    return HIGHLIGHT_MAP.get(file_path.suffix.lower(), 'text')


def get_tags_for_file(file_path: Path) -> List[str]:
    """Devuelve lista de tags TiddlyWiki para `file_path`."""
    # Construir título basado en ruta
    try:
        repo_root = Path(__file__).resolve().parents[1]
        rel = file_path.relative_to(repo_root)
        title = '-' + str(rel).replace(os.sep, '_')
    except Exception:
        title = '-' + file_path.name

    # 1) Tags personalizados
    if title in title_to_tags:
        tags = title_to_tags[title].copy()
    else:
        # 2) Derivar tag de tipo con emoji
        name = file_path.name
        ext = file_path.suffix.lower()
        if name in SPECIAL_FILENAMES:
            base = SPECIAL_FILENAMES[name]
        elif ext in EXTENSION_TAG_MAP:
            base = EXTENSION_TAG_MAP[ext]
        else:
            base = DEFAULT_TAG
        if base == DEFAULT_TAG:
            tags = [f"[[{base}]]"]
        else:
            tags = [f"[[⚙️ {base}]]"]

    # 3) Tag basado en título (sin emoji)
    tags.append(f"[[{title}]]")
    # 4) Tag de grupo sin emoji
    tags.append("[[--- Codigo]]")

    return tags

# CLI de prueba
if __name__ == '__main__':
    import sys
    for arg in sys.argv[1:]:
        p = Path(arg)
        print(p, '->', get_tags_for_file(p))
