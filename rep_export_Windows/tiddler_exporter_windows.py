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
import re
import gzip
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
import argparse
import tag_mapper_windows as tag_mapper
from cli_utils_Windows import safe_print, load_ignore_spec, is_ignored
from detect_root import find_repo_root

# ===== Configuración =====
ROOT_DIR = find_repo_root(Path(__file__))
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "tiddlers-export"
HASH_FILE = SCRIPT_DIR / ".hashes.json"
# Carga spec de .gitignore
IGNORE_SPEC = load_ignore_spec(ROOT_DIR)

# Extensiones válidas: mapea etiquetas y agrega .toml
VALID_EXT = set(tag_mapper.EXTENSION_TAG_MAP.keys()) | {'.toml'}
ALLOWED_NAMES = set(tag_mapper.SPECIAL_FILENAMES.keys())
# Límite de tamaño de archivo para evitar cargar binarios enormes en memoria
MAX_FILE_SIZE_BYTES = int(os.environ.get('REPO_EXPORT_MAX_FILE_SIZE', 1 * 1024 * 1024))  # default 1 MB
PREVIEW_BYTES = 65536  # 64 KB

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


def hash_file_streaming(path: Path) -> str:
    """Calcula SHA-1 en bloques de 64 KB sin cargar el archivo completo en memoria."""
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def safe_title(path: Path) -> str:
    """
    Retorna la ruta relativa natural como display title para TiddlyWiki (separador '/').
    Ejemplo: 'rep_export_Windows/tiddler_exporter_windows.py'
    """
    return path.relative_to(ROOT_DIR).as_posix()


def sanitize_filename(path: Path) -> str:
    """
    Genera un nombre de archivo seguro para disco.
    Solo permite: letras, dígitos, puntos, guiones y guiones bajos.
    Trunca en 200 caracteres añadiendo sufijo de hash para evitar colisiones.
    """
    rel = path.relative_to(ROOT_DIR).as_posix()
    safe = re.sub(r'[^a-zA-Z0-9._-]', '_', rel.replace('/', '_'))
    safe = safe.lstrip('.-_')
    if not safe:
        safe = f"unnamed_{hashlib.sha1(rel.encode()).hexdigest()[:8]}"
    if len(safe) > 200:
        suffix = hashlib.sha1(rel.encode()).hexdigest()[:8]
        safe = safe[:191] + '_' + suffix
    return safe


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

def build_large_tiddler(file: Path, action: str = 'preview', preview_bytes: int = PREVIEW_BYTES) -> dict:
    """
    Crea un tiddler para archivos grandes sin leer todo su contenido.
    action:
      'preview' → primeros preview_bytes como texto.
      'copy'    → metadatos + copia gzip en tiddlers-export/large/.
      'embed'   → contenido completo (solo si se fuerza explícitamente).
    """
    title = safe_title(file)
    tags_semantic = tag_mapper.get_tags_for_file(file)
    rel_path = str(file.relative_to(ROOT_DIR))
    size_bytes = file.stat().st_size

    # Detectar si es binario leyendo los primeros 4 KB
    raw_head = b''
    try:
        with open(file, 'rb') as f:
            raw_head = f.read(4096)
    except OSError:
        pass
    is_binary = b'\x00' in raw_head

    if action == 'embed':
        try:
            content = file.read_text(encoding='utf-8', errors='replace')
        except Exception:
            content = ''
        lang = detect_language(file)
        text = f'```{lang}\n{content}\n```'
    elif action == 'copy':
        large_dir = OUTPUT_DIR / 'large'
        large_dir.mkdir(parents=True, exist_ok=True)
        gz_name = sanitize_filename(file) + '.gz'
        gz_path = large_dir / gz_name
        try:
            with open(file, 'rb') as f_in, gzip.open(gz_path, 'wb') as f_out:
                while True:
                    chunk = f_in.read(65536)
                    if not chunk:
                        break
                    f_out.write(chunk)
            copy_ref = str(gz_path.relative_to(OUTPUT_DIR.parent))
        except Exception as e:
            copy_ref = f'[error al copiar: {e}]'
        text = (
            f'> Archivo grande ({size_bytes/1024:.1f} KB). '
            f'Copia comprimida: `{copy_ref}`'
        )
    else:  # 'preview'
        if is_binary:
            text = f'> Archivo binario ({size_bytes/1024:.1f} KB). Vista previa no disponible.'
        else:
            try:
                preview = raw_head[:preview_bytes].decode('utf-8', errors='replace')
            except Exception:
                preview = ''
            lang = detect_language(file)
            text = (
                f'> Vista previa: primeros {preview_bytes//1024} KB '
                f'de {size_bytes/1024:.1f} KB totales.\n\n'
                f'```{lang}\n{preview}\n```'
            )

    return {
        'title': title,
        'text': text,
        'type': 'text/markdown',
        'tags': ' '.join(tags_semantic),
        'tags_list': tags_semantic,
        'path': rel_path,
        'large_file': True,
        'size_bytes': size_bytes,
        'is_binary': is_binary,
        'large_action': action,
    }


def build_tiddler(file, content, use_new_schema=False):
    title = safe_title(file)
    tags_semantic = tag_mapper.get_tags_for_file(file)
    relations = infer_relations(file, content)
    tags_rel = tags_from_relations(relations)
    all_tags = tags_semantic + tags_rel
    lang = detect_language(file)
    rel_path = str(file.relative_to(ROOT_DIR))
    tiddler = {
        "title": title,
        "text": f"```{lang}\n{content}\n```",   # mantiene compatibilidad TW
        "type": "text/markdown",
        "tags": " ".join(all_tags),             # para TW
        "tags_list": all_tags,                  # para IA
        "relations": relations,                 # para IA
        "hash": calc_hash(content),             # para IA
        "path": rel_path,                       # para IA
        "content_raw": content                  # opcional: texto plano
    }
    return tiddler

def export_tiddlers(
    dry_run: bool = False,
    use_new_schema: bool = False,
    include_large: bool = False,
    large_action: str = 'preview',
    preview_bytes: int = PREVIEW_BYTES,
    max_size: int = None,
):
    effective_max = max_size if max_size is not None else MAX_FILE_SIZE_BYTES
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
        if file.stat().st_size > effective_max:
            if not include_large:
                safe_print(f"[skip] '{rel}' supera el límite de {effective_max // 1024} KB.")
                continue
            # Archivo grande incluido
            h = hash_file_streaming(file)
            new_hashes[rel] = h
            if old_hashes.get(rel) == h:
                continue
            tiddler = build_large_tiddler(file, action=large_action, preview_bytes=preview_bytes)
            out = OUTPUT_DIR / f"{sanitize_filename(file)}.json"
            if dry_run:
                safe_print(f"[dry-run large] {rel}")
            else:
                out.write_text(json.dumps(tiddler, ensure_ascii=False, indent=2), encoding='utf-8')
                safe_print(f"Exported [large/{large_action}]: {rel}")
            changed.append(rel)
            continue
        h = hash_file_streaming(file)
        new_hashes[rel] = h
        if old_hashes.get(rel) == h:
            continue
        try:
            content = file.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        tiddler = build_tiddler(file, content, use_new_schema=use_new_schema)
        out = OUTPUT_DIR / f"{sanitize_filename(file)}.json"
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
    _p = argparse.ArgumentParser(description="Exporta tiddlers JSON del repositorio.")
    _p.add_argument('--dry-run', action='store_true', help="Simular sin escribir archivos.")
    _p.add_argument('--new-schema', action='store_true', help="Usar schema extendido.")
    _p.add_argument('--include-large', action='store_true',
                    help="Incluir archivos grandes (por encima de --max-size).")
    _p.add_argument('--large-action', choices=['preview', 'copy', 'embed'], default='preview',
                    help="Cómo exportar archivos grandes: preview (default) | copy | embed.")
    _p.add_argument('--preview-bytes', type=int, default=PREVIEW_BYTES,
                    help=f"Bytes a incluir en el preview (default {PREVIEW_BYTES}).")
    _p.add_argument('--max-size', type=int, default=None,
                    help="Límite de tamaño en bytes. Sobreescribe MAX_FILE_SIZE_BYTES.")
    _p.add_argument('--root', type=Path, default=None,
                    help="Raíz del repositorio objetivo. Sobreescribe detección automática.")
    _args = _p.parse_args()
    if _args.root:
        ROOT_DIR = Path(_args.root).resolve()
        IGNORE_SPEC = load_ignore_spec(ROOT_DIR)
    export_tiddlers(
        dry_run=_args.dry_run,
        use_new_schema=_args.new_schema,
        include_large=_args.include_large,
        large_action=_args.large_action,
        preview_bytes=_args.preview_bytes,
        max_size=_args.max_size,
    )
