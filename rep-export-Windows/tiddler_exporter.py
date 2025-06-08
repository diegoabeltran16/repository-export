#!/usr/bin/env python3
"""
Script: tiddler_exporter.py (Windows)
Plataforma: Windows

Este script recorre los archivos del repositorio y crea archivos JSON (tiddlers) para TiddlyWiki.
Mejoras:
- Ignora patrones de .gitignore (salvo `estructura.txt`).
- Exporta solo archivos con extensión válida o nombres especiales.
- Detecta cambios usando hashes para exportar únicamente archivos modificados.
- Añade tags semánticos con `tag_mapper.get_tags_for_file`:
  * Tag basado en nombre (`-[ruta_con_underscores]`).
  * Tag de grupo `--- Codigo` (sin emoji).
  * Etiqueta de tipo de código con emoji (⚙️ CSS, ⚙️ Python, etc.).
- Genera bloque Markdown con syntax highlighting adecuado.
- Soporta `--dry-run` para simulación.

Uso:
  python rep-export-Windows/tiddler_exporter.py [--dry-run]
"""
import os
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
import tag_mapper

# ===== Configuración =====
ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "tiddlers-export"
HASH_FILE = SCRIPT_DIR / ".hashes.json"
IGNORE_SPEC = tag_mapper.load_ignore_spec(ROOT_DIR)

# Extensiones y nombres válidos
VALID_EXT = set(tag_mapper.EXTENSION_TAG_MAP.keys())
ALLOWED_NAMES = set(tag_mapper.SPECIAL_FILENAMES.keys())

# ===========================
def get_all_files():
    """
    Genera todos los archivos a exportar:
    - Siempre incluye 'estructura.txt'.
    - Excluye archivos según .gitignore.
    - Filtra por extensiones o nombres especiales.
    """
    for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
        # Evitar directorios internos
        dirnames[:] = [d for d in dirnames if d not in ('tiddler_tag_doc', 'tiddlers-export')]
        for name in filenames:
            path = Path(dirpath) / name
            rel = path.relative_to(ROOT_DIR)
            if str(rel) == 'estructura.txt':
                yield path
                continue
            if IGNORE_SPEC.match_file(str(rel)):
                continue
            if path.suffix.lower() in VALID_EXT or name in ALLOWED_NAMES:
                yield path


def calc_hash(text: str) -> str:
    return hashlib.sha1(text.encode('utf-8')).hexdigest()


def safe_title(path: Path) -> str:
    """
    Convierte ruta en título: prefijo '-' y '_' en lugar de separadores.
    """
    return '-' + str(path.relative_to(ROOT_DIR)).replace(os.sep, '_')


def detect_language(path: Path) -> str:
    return tag_mapper.detect_language(path)


def export_tiddlers(dry_run: bool = False):
    """
    Exporta tiddlers JSON para archivos modificados.
    """
    OUTPUT_DIR.mkdir(exist_ok=True)
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
        # Datos del tiddler
        title = safe_title(file)
        tags = tag_mapper.get_tags_for_file(file)
        lang = detect_language(file)
        text_md = f"## [[Tags]]\n{' '.join(['[['+t.strip('[]')+']]' for t in tags])}\n\n```{lang}\n{content}\n```"
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
            print(f"[dry-run] {rel}")
        else:
            out.write_text(json.dumps(tiddler, ensure_ascii=False, indent=2), encoding='utf-8')
            print(f"Exported: {rel}")
        changed.append(rel)

    if not dry_run:
        HASH_FILE.write_text(json.dumps(new_hashes, indent=2), encoding='utf-8')

    print(f"\n📦 Total cambios: {len(changed)}")
    for c in changed:
        print(f"  - {c}")


if __name__ == '__main__':
    import sys
    dry = '--dry-run' in sys.argv
    export_tiddlers(dry_run=dry)
