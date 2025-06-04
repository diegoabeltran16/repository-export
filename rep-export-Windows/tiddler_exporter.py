#!/usr/bin/env python3
"""
📦 Script: tiddler_exporter.py
🖥️ Plataforma: Windows (PowerShell/Command Prompt)

Función:
Este script recorre todos los archivos fuente del repositorio y detecta cambios
usando hashes para generar archivos `.json` (tiddlers) para TiddlyWiki.
Cada tiddler contiene:
  - Título prefijado con `-` basado en la ruta relativa al repositorio
  - Tags semánticos obtenidos desde `tag_mapper.py`
  - Bloque Markdown con syntax highlighting apropiado según el lenguaje

Mejoras realizadas:
  - Se amplía la lista de extensiones admitidas para incluir lenguajes comunes
  - Mapeos extendidos en `LANGUAGE_MAP` (JS, TS, Java, C, C++, Rust, PHP, etc.)
  - Manejo de archivos especiales como `Dockerfile`, `Makefile`, `.gitignore`, etc.
  - Solo exporta archivos cuyo hash haya cambiado, para eficiencia
  - Compatible con Python 3.7+ en Windows

Uso:
  # Exporta solo archivos modificados
  python scripts/tiddler_exporter.py

  # Modo simulación: muestra qué se actualizaría sin escribir archivos
  python rep-export-Windows\tiddler_exporter.py
"""
import os
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
import tag_mapper  # Debe estar en el mismo directorio o en PATH

# ==========================
# ⚙️ CONFIGURACIÓN GENERAL
# ==========================

# ROOT_DIR apunta a la raíz del repositorio (dos niveles arriba de este script)
ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "tiddlers-export"
HASH_FILE = SCRIPT_DIR / ".hashes.json"

# Extensiones válidas (archivos que se convierten en tiddlers)
VALID_EXTENSIONS = [
    '.py', '.md', '.json', '.sh', '.html', '.css', '.yml', '.yaml', '.txt',
    '.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.cc', '.h', '.hpp',
    '.cs', '.rb', '.go', '.rs', '.php', '.pl', '.lua', '.kt', '.kts', '.swift',
    '.xml', '.sql', '.toml', '.csv', '.ini', '.cfg', '.dockerfile', '.bat', '.ps1'
]
# Nombres de archivos sin extensión que queremos incluir
ALLOWED_FILENAMES = ['.gitignore', 'Dockerfile', 'Makefile', 'README']

# Directorios a ignorar durante la recursión
IGNORE_DIRS = [
    '__pycache__', 'venv', '.venv', 'dist', 'node_modules', 'output', 'input',
    '.pytest_cache', 'configs', 'media', 'project_details', 'tiddlers-export'
]

# Mapeo de extensiones a lenguajes para syntax highlighting en Markdown
LANGUAGE_MAP = {
    '.py': 'python',
    '.md': 'markdown',
    '.json': 'json',
    '.sh': 'bash',
    '.bat': 'batch',
    '.ps1': 'powershell',
    '.yml': 'yaml',
    '.yaml': 'yaml',
    '.html': 'html',
    '.css': 'css',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.java': 'java',
    '.c': 'c',
    '.cpp': 'cpp',
    '.cc': 'cpp',
    '.h': 'cpp',
    '.hpp': 'cpp',
    '.cs': 'csharp',
    '.rb': 'ruby',
    '.go': 'go',
    '.rs': 'rust',
    '.php': 'php',
    '.pl': 'perl',
    '.lua': 'lua',
    '.kt': 'kotlin',
    '.kts': 'kotlin',
    '.swift': 'swift',
    '.xml': 'xml',
    '.sql': 'sql',
    '.toml': 'toml',
    '.csv': 'csv',
    '.ini': 'ini',
    '.cfg': 'cfg'
}

# Archivos especiales a reconocer por nombre
SPECIAL_LANGUAGES = {
    '.gitignore': 'gitignore',
    'Dockerfile': 'dockerfile',
    'Makefile': 'makefile',
    'README': 'markdown'
}

# ==============================
# 🔎 FUNCIONES AUXILIARES
# ==============================

def get_all_files(directory: Path):
    """
    Recorre recursivamente 'directory' y devuelve una lista de Path
    para archivos válidos según VALID_EXTENSIONS o ALLOWED_FILENAMES,
    excluyendo carpetas en IGNORE_DIRS.
    """
    all_files = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for filename in files:
            ext = Path(filename).suffix.lower()
            # Chequea extensiones válidas o nombres especiales (sin extensión)
            if ext in VALID_EXTENSIONS or filename in ALLOWED_FILENAMES:
                all_files.append(Path(root) / filename)
    return all_files

def get_hash(content: str) -> str:
    """
    Calcula el hash SHA-1 de una cadena (usada para detectar cambios).
    """
    return hashlib.sha1(content.encode('utf-8')).hexdigest()

def safe_title(path: Path) -> str:
    """
    Convierte una ruta de archivo en un título válido para tiddler:
    - Prefijo '-' (por convención TiddlyWiki)
    - Reemplaza separadores de ruta por '_'
    Ejemplo: 'src/utils/helper.py' → '-src_utils_helper.py'
    """
    return '-' + str(path.relative_to(ROOT_DIR)).replace(os.sep, '_')

def detect_language(file_path: Path) -> str:
    """
    Determina el lenguaje para el bloque de código en Markdown:
    1. Si el nombre está en SPECIAL_LANGUAGES, lo usa.
    2. En otro caso, busca la extensión en LANGUAGE_MAP.
    3. Por defecto, devuelve 'text'.
    """
    name = file_path.name
    if name in SPECIAL_LANGUAGES:
        return SPECIAL_LANGUAGES[name]
    ext = file_path.suffix.lower()
    return LANGUAGE_MAP.get(ext, 'text')

# ==============================
# 🚀 EXPORTADOR PRINCIPAL
# ==============================

def export_tiddlers(dry_run=False):
    """
    Recorre todos los archivos válidos en ROOT_DIR, calcula sus hashes y
    exporta solo los que cambiaron a la carpeta OUTPUT_DIR.

    - Si dry_run=True, solo imprime qué archivos cambiarían.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Carga hashes previos o inicia vacío
    if HASH_FILE.exists():
        try:
            with open(HASH_FILE, 'r', encoding='utf-8') as f:
                old_hashes = json.load(f)
        except Exception:
            print(f"⚠️ No se pudo leer {HASH_FILE}. Se reiniciarán hashes.")
            old_hashes = {}
    else:
        old_hashes = {}

    new_hashes = {}
    changed_files = []

    for file_path in get_all_files(ROOT_DIR):
        rel_path = str(file_path.relative_to(ROOT_DIR))
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

        # Construir tiddler
        title = safe_title(file_path)
        tags = tag_mapper.get_tags_for_file(file_path)
        lang = detect_language(file_path)

        text_block = (
            "## [[Tags]]\n"
            f"{' '.join(tags)}\n\n"
            f"```{lang}\n{content}\n```"
        )

        tiddler = {
            "title": title,
            "text": text_block,
            "tags": ' '.join(tags),
            "type": "text/markdown",
            "created": datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:17],
            "modified": datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:17],
        }

        if dry_run:
            print(f"[dry-run] Detectado cambio en: {rel_path}")
            continue

        out_file = OUTPUT_DIR / f"{title}.json"
        try:
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump(tiddler, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ No se pudo escribir {out_file}: {e}")
            continue

        changed_files.append(rel_path)

    # Actualizar hashes si no es dry_run
    if not dry_run:
        try:
            with open(HASH_FILE, 'w', encoding='utf-8') as f:
                json.dump(new_hashes, f, indent=2)
        except Exception as e:
            print(f"⚠️ No se pudo escribir {HASH_FILE}: {e}")

    # Informe final
    print(f"\n📦 Archivos modificados: {len(changed_files)}")
    if changed_files:
        for path in changed_files:
            print(f"  ✅ Exportado: {path}")
    else:
        print("  🔁 Sin cambios detectados.")

# ==============================
# 🧪 CLI: Entrada directa
# ==============================

if __name__ == "__main__":
    import sys
    dry = '--dry-run' in sys.argv
    export_tiddlers(dry_run=dry)
