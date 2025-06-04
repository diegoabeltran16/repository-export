#!/usr/bin/env python3
"""
📦 Módulo: tag_mapper.py (Windows)
🎯 Plataforma: Windows

Función
=======
Asigna tags semánticos a cada archivo del repositorio.  
Orden de precedencia:
1. Tags personalizados desde JSON en `tiddler_tag_doc/` (misma carpeta).  
2. Tag derivado por extensión o nombre especial.  
3. Fallback `[[--- 🧬 Por Clasificar]]`.

Los tags devueltos sirven para que el selector de modelo de embeddings elija el
modelo óptimo (Python ⇒ CodeBERT, Markdown ⇒ MiniLM, etc.).

Salida
------
`List[str]` con tags en sintaxis TiddlyWiki (`[[TagName]]`).
"""
import json
import os
from pathlib import Path
from typing import List

# ========================================
# ⚙️ Rutas y carga de JSON personalizados
# ========================================
TIDDLER_TAG_DIR = Path(__file__).resolve().parent / "tiddler_tag_doc"

title_to_tags: dict[str, List[str]] = {}
if TIDDLER_TAG_DIR.exists():
    for json_file in sorted(TIDDLER_TAG_DIR.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    title = item.get("title", "").strip()
                    tags_str = item.get("tags", "").strip()
                    if title and tags_str:
                        title_to_tags[title] = tags_str.split()
        except Exception as e:
            print(f"⚠️ Error leyendo {json_file.name}: {e}")

# ========================================
# 🗂️ Mapeo extensión → Tag
# ========================================
EXTENSION_TAG_MAP = {
    # Code / scripting
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", ".go": "Go", ".rs": "Rust",
    ".java": "Java", ".c": "C", ".cpp": "C++", ".cc": "C++", ".hpp": "C++",
    ".rb": "Ruby", ".php": "PHP", ".kt": "Kotlin", ".swift": "Swift",
    ".sh": "Shell", ".bash": "Shell", ".ps1": "PowerShell", ".bat": "Batch",
    ".lua": "Lua", ".pl": "Perl",
    # Markup / data
    ".md": "Markdown", ".rst": "reStructuredText", ".html": "HTML", ".htm": "HTML",
    ".css": "CSS", ".xml": "XML", ".json": "JSON", ".yml": "YAML", ".yaml": "YAML",
    ".toml": "TOML", ".csv": "CSV", ".sql": "SQL",
    # Bio‑informática
    ".fasta": "BioSeq", ".fastq": "BioSeq", ".vcf": "VCF", ".pdb": "Protein3D",
    # Docs & others
    ".tex": "LaTeX", ".cfg": "Config", ".ini": "Config", ".log": "Log", ".txt": "Text"
}

SPECIAL_FILENAMES = {
    "Dockerfile": "Dockerfile",
    "Makefile": "Makefile",
    "README": "README",
    "LICENSE": "License"
}

DEFAULT_TAG = "--- 🧬 Por Clasificar"

# ========================================
# 🔎 API principal
# ========================================

def get_tags_for_file(file_path: Path) -> List[str]:
    """Devuelve lista de tags TiddlyWiki para `file_path`."""
    # Construir título estándar (-ruta_con_guiones)
    try:
        root_dir = Path(__file__).resolve().parents[1]
        rel_title = "-" + str(file_path.relative_to(root_dir)).replace(os.sep, "_")
    except Exception:
        rel_title = "-" + file_path.name

    # 1) ¿Existe en JSON personalizados?
    if rel_title in title_to_tags:
        return title_to_tags[rel_title]

    # 2) Derivar por extensión / nombre
    name = file_path.name
    ext = file_path.suffix.lower()
    if name in SPECIAL_FILENAMES:
        tag = SPECIAL_FILENAMES[name]
    elif ext in EXTENSION_TAG_MAP:
        tag = EXTENSION_TAG_MAP[ext]
    else:
        tag = DEFAULT_TAG

    return [f"[[{tag}]]"]

# CLI para pruebas rápidas
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python tag_mapper.py <ruta_archivo>")
        sys.exit(1)
    path = Path(sys.argv[1])
    print(get_tags_for_file(path))
