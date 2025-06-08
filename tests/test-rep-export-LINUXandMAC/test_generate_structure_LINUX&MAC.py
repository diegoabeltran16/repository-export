#!/usr/bin/env python3
"""
Script: tiddler_exporter.py (Linux/macOS)
Plataforma: Linux, macOS

Este script recorre los archivos del repositorio y genera archivos JSON (tiddlers) para TiddlyWiki.
Mejoras:
- Ignora patrones de .gitignore (salvo `estructura.txt`).
- Exporta solo archivos con extensiones válidas o nombres especiales.
- Detecta cambios usando hashes para exportar solo archivos modificados.
- Añade tags semánticos con `tag_mapper.get_tags_for_file`:
  * Tag de tipo con emoji ⚙️ (p.ej. ⚙️ Python).
  * Tag basado en nombre `-ruta_con_underscores` sin emoji.
  * Tag de grupo `--- Codigo`.
- Genera bloque Markdown con syntax highlighting adecuado desde `tag_mapper.detect_language`.
- Soporta `--dry-run` para simulación.

Uso:
  python3 tiddler_exporter.py [--dry-run]
"""

import os
import sys
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

# Asegurarnos de poder importar tag_mapper desde esta carpeta
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import tag_mapper  # noqa: E402

# ===== Configuración =====
ROOT_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = SCRIPT_DIR / "tiddlers-export"
HASH_FILE = SCRIPT_DIR / ".hashes.json"
IGNORE_SPEC = tag_mapper.load_ignore_spec(ROOT_DIR)

# Extensiones y nombres permitidos
VALID_EXT = set(tag_mapper.EXTENSION_TAG_MAP.keys())
ALLOWED_NAMES = set(tag_mapper.SPECIAL_FILENAMES.keys())

def get_all_files():
    """
    Recorre ROOT_DIR y devuelve archivos a exportar:
      - Siempre incluye `estructura.txt`.
      - Excluye según .gitignore (IGNORE_SPEC).
      - Filtra por extensiones y nombres especiales.
    """
    for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
        # No entrar en nuestros propios directorios de tiddlers ni de tags
        dirnames[:] = [d for d in dirnames if d not in ('tiddler_tag_doc', 'tiddlers-export')]
        for name in filenames:
            path = Path(dirpath) / name
            rel = str(path.relative_to(ROOT_DIR))
            if rel == 'estructura.txt':
                yield path
                continue
            if IGNORE_SPEC.match_file(rel):
                continue
            if path.suffix.lower() in VALID_EXT or name in ALLOWED_NAMES:
                yield path

def calc_hash(content: str) -> str:
    return hashlib.sha1(content.encode('utf-8')).hexdigest()

def safe_title(path: Path) -> str:
    """Convierte ruta en título: `-ruta_con_guiones`."""
    return '-' + str(path.relative_to(ROOT_DIR)).replace(os.sep, '_')

def export_tiddlers(dry_run: bool = False):
    """
    Exporta tiddlers JSON para archivos nuevos o modificados.
    """
    OUTPUT_DIR.mkdir(exist_ok=True)
    # Cargar hashes anteriores
    old_hashes = {}
    if HASH_FILE.exists():
        try:
            old_hashes = json.loads(HASH_FILE.read_text(encoding='utf-8'))
        except Exception:
            old_hashes = {}
    new_hashes = {}
    changed = []

    for file in get_all_files():
        rel = str(file.relative_to(ROOT_DIR))
        content = file.read_text(encoding='utf-8', errors='replace')
        h = calc_hash(content)
        new_hashes[rel] = h
        if old_hashes.get(rel) == h:
            continue

        title = safe_title(file)
        tags = tag_mapper.get_tags_for_file(file)
        lang = tag_mapper.detect_language(file)
        text_md = (
            "## [[Tags]]\n"
            f"{' '.join(tags)}\n\n"
            f"```{lang}\n{content}\n```"
        )

        tiddler = {
            'title': title,
            'text': text_md,
            'tags': ' '.join(tags),
            'type': 'text/markdown',
            'created': datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:17],
            'modified': datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:17]
        }

        out_file = OUTPUT_DIR / f"{title}.json"
        if dry_run:
            print(f"[dry-run] {rel}")
        else:
            out_file.write_text(json.dumps(tiddler, ensure_ascii=False, indent=2), encoding='utf-8')
            print(f"Exported: {rel}")
        changed.append(rel)

    if not dry_run:
        HASH_FILE.write_text(json.dumps(new_hashes, indent=2), encoding='utf-8')

    print(f"\nTotal cambios: {len(changed)}")
    for c in changed:
        print(f"  - {c}")

if __name__ == '__main__':
    dry = '--dry-run' in sys.argv
    export_tiddlers(dry_run=dry)
