#!/usr/bin/env python3
"""
Script: tiddler_exporter_UNIX.py (Linux/macOS)
Plataforma: Linux, macOS

Este script recorre los archivos del repositorio y genera archivos JSON (tiddlers) para TiddlyWiki.
Mejoras:
- Ignora patrones de .gitignore (salvo `estructura.txt` y `.gitignore`).
- Exporta solo archivos con extensiones válidas o nombres especiales, incluyendo `.toml`.
- Detecta cambios usando hashes para exportar solo archivos modificados.
- Añade tags semánticos con `tag_mapper_UNIX.get_tags_for_file`:
  * Tag de tipo con emoji ⚙️ (p.ej. ⚙️ Python).
  * Tag basado en nombre `-ruta_con_underscores` sin emoji.
  * Tag de grupo `--- Codigo`.
- Genera bloque Markdown con syntax highlighting adecuado desde `tag_mapper_UNIX.detect_language`.
- Soporta `--dry-run` para simulación.

Uso:
  python3 tiddler_exporter_UNIX.py [--dry-run]
"""
import os
import sys
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
import tag_mapper_UNIX
from tag_mapper_UNIX import load_ignore_spec, detect_language
from rep_export_LINUXandMAC.cli_utils_UNIX import safe_print

# ===== Configuración =====
ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "tiddlers-export"
HASH_FILE = SCRIPT_DIR / ".hashes.json"
IGNORE_SPEC = load_ignore_spec(ROOT_DIR)

VALID_EXT = set(tag_mapper_UNIX.EXTENSION_TAG_MAP.keys()) | {'.toml'}
ALLOWED_NAMES = set(tag_mapper_UNIX.SPECIAL_FILENAMES.keys())

def get_all_files():
    """
    Genera todos los archivos a exportar:
    - Siempre incluye 'estructura.txt' y '.gitignore'.
    - Excluye archivos según .gitignore.
    - Filtra por extensiones válidas o nombres especiales.
    """
    for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
        # Evitar directorios de export/data
        dirnames[:] = [d for d in dirnames if d not in ('tiddlers-export', 'tiddler_tag_doc')]
        for name in filenames:
            path = Path(dirpath) / name
            rel = str(path.relative_to(ROOT_DIR))
            # Siempre incluir estos
            if rel in ('estructura.txt', '.gitignore'):
                yield path
                continue
            # Skip según .gitignore
            if IGNORE_SPEC and IGNORE_SPEC.match_file(rel):
                continue
            # Extensiones y nombres permitidos
            if path.suffix.lower() in VALID_EXT or name in ALLOWED_NAMES:
                yield path

def calc_hash(content: str) -> str:
    return hashlib.sha1(content.encode('utf-8')).hexdigest()

def safe_title(path: Path) -> str:
    """
    Convierte ruta en título: prefijo '-' y '_' en lugar de separadores.
    """
    return '-' + str(path.relative_to(ROOT_DIR)).replace(os.sep, '_')

def export_tiddlers(dry_run: bool = False):
    """
    Exporta tiddlers JSON para archivos modificados.
    """
    OUTPUT_DIR.mkdir(exist_ok=True)
    # Carga hashes previos
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
        try:
            content = file.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        h = calc_hash(content)
        new_hashes[rel] = h
        if old_hashes.get(rel) == h:
            continue
        title = safe_title(file)
        tags = tag_mapper_UNIX.get_tags_for_file(file)
        lang = detect_language(file)
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
        out = OUTPUT_DIR / f"{title}.json"
        if dry_run:
            safe_print(f"[dry-run] {rel}")
        else:
            out.write_text(json.dumps(tiddler, ensure_ascii=False, indent=2), encoding='utf-8')
            safe_print(f"Exported: {rel}")
        changed.append(rel)

    if not dry_run:
        HASH_FILE.write_text(json.dumps(new_hashes, indent=2), encoding='utf-8')

    # Reporte final
    safe_print(f"\nTotal cambios: {len(changed)}")
    for c in changed:
        safe_print(f"  - {c}")

if __name__ == '__main__':
    dry = '--dry-run' in sys.argv
    export_tiddlers(dry_run=dry)
