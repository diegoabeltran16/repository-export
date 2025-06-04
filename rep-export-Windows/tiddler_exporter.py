"""
📦 Script: tiddler_exporter.py
📍 Ubicación: scripts/tiddler_exporter.py

🧠 Función:
Este script recorre todos los archivos fuente del proyecto, detecta si su contenido ha cambiado,
y si es así, genera un archivo `.json` en formato TiddlyWiki listo para ser importado.

🔖 Cada archivo se convierte en un "tiddler", con:
  - Nombre prefijado con `-` (ej: -src_logger.py)
  - Tags semánticos desde `OpenPages.json` vía `tag_mapper.py`
  - Bloque markdown con código resaltado según lenguaje

🎯 Compatible con TiddlyWiki, offline, AI-ready y 100% Python puro.

✅ Cómo ejecutarlo:

    # Exporta solo si hay cambios
    python rep-export-Windows/tiddler_exporter.py

    # Modo simulación (muestra qué archivos cambiarían)
    python rep-export-Windows/tiddler_exporter.py --dry-run
"""

import os
import json
import hashlib
import tag_mapper
from datetime import datetime, timezone
from pathlib import Path
from typing import List

# ==========================
# ⚙️ CONFIGURACIÓN GENERAL
# ==========================

ROOT_DIR = Path(__file__).resolve().parents[1]  # raíz del repo
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "tiddlers-export"
HASH_FILE = SCRIPT_DIR / ".hashes.json"

VALID_EXTENSIONS = ['.py', '.md', '.json', '.sh', '.html', '.css', '.yml', '.txt']
ALLOWED_FILENAMES = ['.gitignore']  # Archivos sin extensión pero importantes

IGNORE_DIRS = [
    '__pycache__', 'venv', '.venv', 'dist', 'node_modules', 'output', 'input',
    '.pytest_cache', 'configs', 'media', 'project_details', 'tiddlers-export'
]

LANGUAGE_MAP = {
    '.py': 'python',
    '.md': 'markdown',
    '.json': 'json',
    '.sh': 'bash',
    '.yml': 'bash',
    '.html': 'html',
    '.txt': 'txt',
    '.css': 'css'
}

SPECIAL_LANGUAGES = {
    '.gitignore': 'gitignore'
}

# ==============================
# 🔎 FUNCIONES AUXILIARES
# ==============================

def get_all_files(directory: Path) -> List[Path]:
    """Recorre el proyecto y devuelve archivos válidos para exportar."""
    all_files = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            ext = Path(file).suffix
            if ext in VALID_EXTENSIONS or file in ALLOWED_FILENAMES:
                all_files.append(Path(root) / file)
    return all_files

def get_hash(content: str) -> str:
    """Genera hash SHA-1 para detectar cambios en el archivo."""
    return hashlib.sha1(content.encode('utf-8')).hexdigest()

def safe_title(path: Path) -> str:
    """Convierte una ruta en título de tiddler válido, prefijado con '-'."""
    return '-' + str(path.relative_to(ROOT_DIR)).replace(os.sep, '_')

def detect_language(file_path: Path) -> str:
    """Detecta el lenguaje para resaltar el bloque de código en markdown."""
    if file_path.name in SPECIAL_LANGUAGES:
        return SPECIAL_LANGUAGES[file_path.name]
    ext = file_path.suffix
    return LANGUAGE_MAP.get(ext, 'text')

# ==============================
# 🚀 EXPORTADOR PRINCIPAL
# ==============================

def export_tiddlers(dry_run=False):
    """Recorre los archivos, detecta cambios y genera tiddlers si es necesario."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if HASH_FILE.exists():
        with open(HASH_FILE, 'r', encoding='utf-8') as f:
            old_hashes = json.load(f)
    else:
        old_hashes = {}

    new_hashes = {}
    changed_files = []

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

        if old_hashes.get(rel_path) == hash_now:
            continue  # sin cambios

        title = safe_title(file_path)
        tags = tag_mapper.get_tags_for_file(file_path)  # 🧬 Tags desde OpenPages.json

        # 🧠 Contenido markdown con tags visuales arriba
        text_block = f"## [[Tags]]\n{' '.join(tags)}\n\n```{lang}\n{content}\n```"

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
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(tiddler, f, indent=2, ensure_ascii=False)

        changed_files.append(rel_path)

    if not dry_run:
        with open(HASH_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_hashes, f, indent=2)

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