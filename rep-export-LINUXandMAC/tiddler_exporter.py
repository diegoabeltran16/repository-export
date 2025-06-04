#!/usr/bin/env python3
"""
📦 Script: tiddler_exporter.py
🖥️ Plataforma: Linux / macOS

Función:
Este script recorre todos los archivos fuente de un repositorio, detecta cambios
usando hashes, y genera archivos `.json` que actúan como tiddlers para TiddlyWiki.
Cada tiddler contiene:
  - Título prefijado con `-` basado en la ruta relativa
  - Tags semánticos
  - Bloque Markdown con syntax highlighting según el lenguaje detectado
  - Metadatos de creación y modificación

Mejoras:
- Se han ampliado las extensiones de archivos admitidas para incluir los lenguajes
  de programación más comunes: JavaScript, TypeScript, Java, C, C++, Rust, Ruby,
  PHP, SQL, XML, TOML, Lua, Perl, Kotlin, Swift, Shell, Powershell, Dockerfile,
  Makefile, Markdown, JSON, YAML, CSS, SCSS, HTML, CSV y más.
- Se han incluido nombres especiales (sin extensión) como `Dockerfile`, `Makefile`.
- Lenguajes mapeados para syntax highlighting en TiddlyWiki ampliados.

Uso:
  # Exporta solo si cambió el contenido
  python3 tiddler_exporter.py

  # Simulación: solo muestra qué archivos cambiarían
  python3 tiddler_exporter.py --dry-run
  
  # Cambiar directorio raíz y carpeta de salida:
  python3 tiddler_exporter.py --root /ruta/proyecto --output /ruta/tiddlers
"""

import os
import json
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List

# ==========================
# ⚙️ CONFIGURACIÓN GENERAL
# ==========================

# Si el script se invoca directamente, __file__ está definido
# ROOT_DIR apunta a la carpeta raíz del repositorio (un nivel arriba)
# Permite pasar --root para personalizarlo

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Exporta archivos del repositorio como tiddlers JSON.")
    parser.add_argument('--root', type=str, default=None,
                        help='Carpeta raíz del repositorio. Por defecto, la carpeta Padre de este script.')
    parser.add_argument('--output', type=str, default=None,
                        help='Carpeta donde se guardarán los tiddlers. Por defecto, ./tiddlers-export dentro de este script.')
    parser.add_argument('--dry-run', action='store_true',
                        help='Solo muestra qué archivos cambiarían, sin escribir nada.')
    parser.add_argument('--ignore', type=str, nargs='*', default=None,
                        help='Lista adicional de carpetas para ignorar. Ej: --ignore node_modules dist')
    return parser.parse_args()

args = parse_args()

# Determinar ROOT_DIR
if args.root:
    ROOT_DIR = Path(args.root).resolve()
else:
    ROOT_DIR = Path(__file__).resolve().parents[1]

# Determinar SCRIPT_DIR y default OUTPUT_DIR
SCRIPT_DIR = Path(__file__).parent
if args.output:
    OUTPUT_DIR = Path(args.output).resolve()
else:
    OUTPUT_DIR = SCRIPT_DIR / "tiddlers-export"

HASH_FILE = SCRIPT_DIR / ".hashes.json"

# ==========================
# 🔖 Extensiones y lenguajes
# ==========================

# Extensiones de archivos válidas (se incluirán en los tiddlers)
VALID_EXTENSIONS = [
    # Lenguajes de script / código
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.h', '.cpp', '.hpp', '.cc', '.hh',
    '.rs', '.rb', '.php', '.go', '.kt', '.kts', '.swift', '.lua', '.pl',
    # Lenguajes de marcado / datos
    '.md', '.mk', '.json', '.yaml', '.yml', '.xml', '.toml', '.csv',
    # Archivos de configuración / scripts
    '.sh', '.bash', '.zsh', '.fish', '.ps1', '.psm1',
    # Estilos y frontend
    '.html', '.htm', '.css', '.scss', '.sass', '.less',
    # Otros comunes
    '.sql', '.Dockerfile', '.Makefile', '.env', '.ini',
    # Archivos de texto genéricos
    '.txt',
]

# Archivos sin extensión que también queremos incluir
ALLOWED_FILENAMES = [
    'Dockerfile', 'Makefile', '.gitignore',
    'README', 'LICENSE',
]

# Mapeo para determinar el lenguaje de resaltado en Markdown
# (extensión → nombre de lenguaje para syntax highlighting)
LANGUAGE_MAP = {
    # Python
    '.py': 'python',
    # JavaScript / TypeScript
    '.js': 'javascript', '.jsx': 'javascript',
    '.ts': 'typescript', '.tsx': 'typescript',
    # Java
    '.java': 'java',
    # C / C++
    '.c': 'c', '.h': 'c', '.cpp': 'cpp', '.cc': 'cpp', '.hpp': 'cpp', '.hh': 'cpp',
    # Rust
    '.rs': 'rust',
    # Ruby
    '.rb': 'ruby',
    # PHP
    '.php': 'php',
    # Go
    '.go': 'go',
    # Kotlin
    '.kt': 'kotlin', '.kts': 'kotlin',
    # Swift
    '.swift': 'swift',
    # Lua
    '.lua': 'lua',
    # Perl
    '.pl': 'perl',
    # Markdown
    '.md': 'markdown', '.mk': 'markdown',
    # JSON, YAML
    '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml',
    # XML, TOML
    '.xml': 'xml', '.toml': 'toml',
    # CSV
    '.csv': 'csv',
    # HTML, CSS
    '.html': 'html', '.htm': 'html',
    '.css': 'css', '.scss': 'scss', '.sass': 'sass', '.less': 'less',
    # SQL
    '.sql': 'sql',
    # Shell
    '.sh': 'bash', '.bash': 'bash', '.zsh': 'bash', '.fish': 'bash',
    # PowerShell
    '.ps1': 'powershell', '.psm1': 'powershell',
    # Archivos especiales
    'Dockerfile': 'dockerfile', 'Makefile': 'makefile',
    # Archivos de texto y configuración simples
    '.txt': 'text', '.env': 'text', '.ini': 'text',
}

# ==========================
# 🔎 Funciones auxiliares
# ==========================

def get_all_files(directory: Path) -> List[Path]:
    """
    Recorre el directorio recursivamente y devuelve archivos válidos
    según VALID_EXTENSIONS o ALLOWED_FILENAMES, ignorando carpetas definidas.
    """
    all_files: List[Path] = []
    # Carpeta estándar a ignorar
    IGNORE_DIRS = {
        '__pycache__', 'venv', '.venv', 'dist', 'node_modules', 'output', 'input',
        '.pytest_cache', 'configs', 'media', 'project_details', 'tiddlers-export'
    }
    # Añadir ignores personalizados si se provén por CLI
    if args.ignore:
        IGNORE_DIRS.update(set(args.ignore))

    for root, dirs, files in os.walk(directory):
        # Filtrar carpetas ignoradas
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for filename in files:
            ext = Path(filename).suffix
            if ext in VALID_EXTENSIONS or filename in ALLOWED_FILENAMES:
                all_files.append(Path(root) / filename)
    return all_files


def get_hash(content: str) -> str:
    """
    Genera hash SHA-1 para detectar cambios en el contenido del archivo.
    """
    return hashlib.sha1(content.encode('utf-8')).hexdigest()


def safe_title(path: Path) -> str:
    """
    Convierte una ruta en un título de tiddler válido (prefijo `-`, guiones bajos).
    Ej: '/repo/src/utils/helpers.py' → '-src_utils_helpers.py'
    """
    return '-' + str(path.relative_to(ROOT_DIR)).replace(os.sep, '_')


def detect_language(file_path: Path) -> str:
    """
    Detecta el lenguaje para syntax highlighting.
    1) Si el nombre (sin extensión) está en LANGUAGE_MAP, lo retorna.
    2) Si la extensión está en LANGUAGE_MAP, la retorna.
    3) Por defecto, usa 'text'.
    """
    name = file_path.name
    # Caso: Dockerfile, Makefile u otro sin extensión
    if name in LANGUAGE_MAP:
        return LANGUAGE_MAP[name]

    ext = file_path.suffix
    return LANGUAGE_MAP.get(ext, 'text')

# ==========================
# 🚀 Exportador principal
# ==========================

def export_tiddlers(dry_run: bool = False):
    """
    Recorre todos los archivos válidos, detecta cambios y genera tiddlers JSON.

    Params:
      dry_run: si es True, solo imprime archivos que cambiarían, sin escribir.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Cargar hashes previos o iniciar vacío
    if HASH_FILE.exists():
        try:
            with open(HASH_FILE, 'r', encoding='utf-8') as f:
                old_hashes = json.load(f)
        except Exception:
            print(f"⚠️ No se pudo leer {HASH_FILE}. Reiniciando hashes.")
            old_hashes = {}
    else:
        old_hashes = {}

    new_hashes: dict[str, str] = {}
    changed_files: List[str] = []

    for file_path in get_all_files(ROOT_DIR):
        rel_path = str(file_path.relative_to(ROOT_DIR))
        lang = detect_language(file_path)

        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"⚠️ Error leyendo {rel_path}: {e}")
            continue

        hash_now = get_hash(content)
        new_hashes[rel_path] = hash_now

        # Si no cambió, saltar
        if old_hashes.get(rel_path) == hash_now:
            continue

        # Construir título y tags
        title = safe_title(file_path)
        try:
            from tag_mapper import get_tags_for_file
            tags_list = get_tags_for_file(file_path)
        except Exception:
            tags_list = ['[[--- 🧬 Por Clasificar]]']
        tags_joined = ' '.join(tags_list)

        # Construir bloque Markdown
        text_block = (
            "## [[Tags]]\n"
            f"{tags_joined}\n\n"
            f"```{lang}\n{content}\n```"
        )

        # Estructura del tiddler
        tiddler = {
            "title": title,
            "text": text_block,
            "tags": tags_joined,
            "type": "text/markdown",
            "created": datetime.now(timezone.utc).strftime('%Y%m%d%H%M%SZ'),
            "modified": datetime.now(timezone.utc).strftime('%Y%m%d%H%M%SZ'),
        }

        if dry_run:
            print(f"[dry-run] Cambios detectados en: {rel_path}")
            continue

        out_file = OUTPUT_DIR / f"{title}.json"
        try:
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump(tiddler, f, indent=2, ensure_ascii=False)
            changed_files.append(rel_path)
        except Exception as e:
            print(f"⚠️ No se pudo escribir {out_file}: {e}")

    # Actualizar hashes si no es dry-run
    if not dry_run:
        try:
            with open(HASH_FILE, 'w', encoding='utf-8') as f:
                json.dump(new_hashes, f, indent=2)
        except Exception as e:
            print(f"⚠️ No se pudo actualizar {HASH_FILE}: {e}")

    # Informe final
    print(f"\n📦 Archivos modificados: {len(changed_files)}")
    if changed_files:
        for path in changed_files:
            print(f"  ✅ Exportado: {path}")
    else:
        print("  🔁 Sin cambios detectados.")


# ==========================
# 🧪 Entrada directa CLI
# ==========================

if __name__ == "__main__":
    export_tiddlers(dry_run=args.dry_run)
