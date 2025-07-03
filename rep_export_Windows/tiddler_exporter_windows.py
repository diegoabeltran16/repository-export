#!/usr/bin/env python3
"""
Script: tiddler_exporter.py (Windows)
Plataforma: Windows

Este script recorre los archivos del repositorio y crea archivos JSON (tiddlers) para TiddlyWiki.
Mejoras:
- Ignora patrones de .gitignore (salvo `estructura.txt` y `.gitignore`).
- Exporta solo archivos con extensión válida o nombres especiales, incluyendo `.toml`.
- Detecta cambios usando hashes para exportar únicamente archivos modificados.
- Añade tags semánticos con `tag_mapper.get_tags_for_file`:
  * Tag basado en ruta (`-[ruta_con_underscores]`).
  * Tag de grupo `--- Codigo`.
  * Etiqueta de tipo de código con emoji (⚙️ Python, ⚙️ TOML, etc.).
- Genera bloque Markdown con syntax highlighting adecuado.
- Soporta `--dry-run` para simulación.

Uso:
  python rep-export-Windows/tiddler_exporter.py [--dry-run]
"""
import os
import sys
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
import tag_mapper_windows as tag_mapper
from cli_utils_Windows import safe_print, load_ignore_spec, is_ignored

# ===== Configuración =====
ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "tiddlers-export"
HASH_FILE = SCRIPT_DIR / ".hashes.json"
# Carga spec de .gitignore
IGNORE_SPEC = load_ignore_spec(ROOT_DIR)

# Extensiones válidas: mapea etiquetas y agrega .toml
VALID_EXT = set(tag_mapper.EXTENSION_TAG_MAP.keys()) | {'.toml'}
ALLOWED_NAMES = set(tag_mapper.SPECIAL_FILENAMES.keys())

# ============================
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


def detect_language(path: Path) -> str:
    """
    Detecta lenguaje para syntax highlighting.
    """
    ext = path.suffix.lower().lstrip('.')
    # Toml, Python, etc.
    return tag_mapper.EXTENSION_TAG_MAP.get(path.suffix.lower(), ext)


def infer_relations(file: Path, content: str):
    """
    Genera relaciones automáticas para el tiddler según reglas y vocabulario estándar.
    """
    relations = {
        "parte_de": ["--- Codigo"]
    }
    rel_path = file.relative_to(ROOT_DIR)
    if len(rel_path.parts) > 1:
        relations["parte_de"].append(rel_path.parts[0])

    # define: ejecutables principales o artefactos conocidos
    if file.name in ("generate_structure.py", "tiddler_exporter.py"):
        relations["define"] = [file.stem]
    if file.suffix.lower() in (".txt", ".json", ".md", ".toml"):
        relations.setdefault("define", []).append(file.name)

    # usa: para Python, busca imports
    if file.suffix.lower() == ".py":
        usa = []
        for line in content.splitlines():
            if line.strip().startswith("import ") or line.strip().startswith("from "):
                tokens = line.replace(",", " ").split()
                for token in tokens:
                    if token in ("import", "from"):
                        continue
                    if token.endswith(".py"):
                        usa.append(token.replace(".py", ""))
                    elif token.isidentifier() and not token.startswith("__"):
                        usa.append(token)
        if usa:
            relations["usa"] = sorted(set(usa))

    # requiere: busca comentarios tipo # @requiere: modulo
    requiere = []
    for line in content.splitlines():
        if "# @requiere:" in line:
            requiere += [x.strip() for x in line.split(":", 1)[1].split(",")]
    if requiere:
        relations["requiere"] = sorted(set(requiere))

    # alternativa_a, no_combinar_con, reemplaza: busca anotaciones en comentarios
    for rel in ["alternativa_a", "no_combinar_con", "reemplaza"]:
        found = []
        for line in content.splitlines():
            if f"# @{rel}:" in line:
                found += [x.strip() for x in line.split(":", 1)[1].split(",")]
        if found:
            relations[rel] = sorted(set(found))

    # --- HEURÍSTICAS AUTOMÁTICAS ---

    # Heurística: Si el nombre contiene 'legacy' o 'old', sugiere alternativa_a con archivos similares sin ese prefijo
    fname = file.stem.lower()
    if any(x in fname for x in ("legacy", "old", "v1")):
        alt_candidates = []
        base = fname.replace("legacy", "").replace("old", "").replace("v1", "")
        for sibling in file.parent.glob("*.py"):
            sname = sibling.stem.lower()
            if sibling != file and base and base in sname and not any(x in sname for x in ("legacy", "old", "v1")):
                alt_candidates.append(sibling.name)
        if alt_candidates:
            relations.setdefault("alternativa_a", []).extend(sorted(set(alt_candidates)))

    # Heurística: Si el nombre contiene 'new', 'modern', 'v2', sugiere reemplaza a archivos similares con 'legacy', 'old', 'v1'
    if any(x in fname for x in ("new", "modern", "v2")):
        repl_candidates = []
        base = fname.replace("new", "").replace("modern", "").replace("v2", "")
        for sibling in file.parent.glob("*.py"):
            sname = sibling.stem.lower()
            if sibling != file and base and base in sname and any(x in sname for x in ("legacy", "old", "v1")):
                repl_candidates.append(sibling.name)
        if repl_candidates:
            relations.setdefault("reemplaza", []).extend(sorted(set(repl_candidates)))

    # Heurística: Si el archivo genera el mismo artefacto que otro, sugiere no_combinar_con
    # (Ejemplo: dos scripts que generan 'estructura.txt')
    if "define" in relations:
        for sibling in file.parent.glob("*.py"):
            if sibling == file:
                continue
            try:
                sibling_content = sibling.read_text(encoding='utf-8', errors='replace')
            except Exception:
                continue
            sib_rels = infer_relations(sibling, sibling_content)
            if "define" in sib_rels and set(relations["define"]) & set(sib_rels["define"]):
                relations.setdefault("no_combinar_con", []).append(sibling.name)

    # Limpia duplicados en todas las relaciones
    for k in relations:
        if isinstance(relations[k], list):
            relations[k] = sorted(set(relations[k]))

    return relations

def tags_from_relations(relations):
    """
    Convierte relaciones en tags tipo [[define:...]] [[usa:...]] [[parte_de:...]]
    """
    tags = []
    for rel, values in relations.items():
        for v in values:
            tags.append(f"[[{rel}:{v}]]")
    return tags

def build_tiddler(file, content, use_new_schema=False):
    title = safe_title(file)
    tags_semantic = tag_mapper.get_tags_for_file(file)
    relations = infer_relations(file, content)
    tags_rel = tags_from_relations(relations)
    all_tags = tags_semantic + tags_rel
    lang = detect_language(file)
    # Relational block as pretty JSON
    rel_block = json.dumps(relations, ensure_ascii=False, indent=2)
    tiddler = {
        "title": title,
        "text": f"RELATIONS:\n{rel_block}\n\n```{lang}\n{content}\n```",
        "type": "text",
        "tags": " ".join(all_tags),
        "tags_list": all_tags,
        "relations": relations
    }
    return tiddler

def export_tiddlers(dry_run: bool = False, use_new_schema: bool = False):
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
        try:
            content = file.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        h = calc_hash(content)
        new_hashes[rel] = h
        if old_hashes.get(rel) == h:
            continue
        tiddler = build_tiddler(file, content, use_new_schema=use_new_schema)
        out = OUTPUT_DIR / f"{tiddler['title']}.json"
        if dry_run:
            safe_print(f"[dry-run] {rel}")
        else:
            out.write_text(json.dumps(tiddler, ensure_ascii=False, indent=2), encoding='utf-8')
            safe_print(f"Exported: {rel}")
        changed.append(rel)

    if not dry_run:
        HASH_FILE.write_text(json.dumps(new_hashes, indent=2), encoding='utf-8')

    safe_print(f"\nTotal cambios: {len(changed)}")
    for c in changed:
        safe_print(f"  - {c}")


if __name__ == '__main__':
    dry = '--dry-run' in sys.argv
    use_new_schema = '--new-schema' in sys.argv
    export_tiddlers(dry_run=dry, use_new_schema=use_new_schema)
