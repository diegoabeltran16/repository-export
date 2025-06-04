"""
📦 Módulo: tag_mapper.py — versión extendida
🎯 Plataforma: Linux / macOS

Descripción
===========
Asigna tags semánticos a los archivos del repositorio para que el sistema de
embeddings pueda elegir el *modelo óptimo* según el tipo de contenido.

Orden de precedencia para asignar tags
-------------------------------------
1. **Tags personalizados** definidos en JSON dentro de `tiddler_tag_doc/`.
2. **Tags automáticos** basados en la extensión o nombre especial del archivo.
3. Fallback: `[[--- 🧬 Por Clasificar]]`.

Ejemplo de salida
-----------------
```
['[[Python]]']                 # para .py
['[[Markdown]]']               # para .md
['[[BioInfo]]']                # para .vcf o .fasta
['[[Modelo Simbólico]]']       # para .iching o nota simbólica
```

Estos tags serán consumidos por `model_selector.py` para decidir si usar un
modelo de lenguaje general, de código, biomédico o simbólico.
"""

import json
from pathlib import Path
import os
from typing import List

# ==============================
# 1. Cargar JSON personalizados
# ==============================
TIDDLER_TAG_DIR = Path(__file__).resolve().parent / "tiddler_tag_doc"
custom_tags: List[dict] = []

def _load_custom_tags():
    if not TIDDLER_TAG_DIR.exists():
        return
    for json_file in sorted(TIDDLER_TAG_DIR.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                custom_tags.extend(data)
        except Exception:
            print(f"⚠️ No se pudo leer {json_file}")

_load_custom_tags()
TITLE_TO_TAGS = {
    item.get("title", "").strip(): item.get("tags", "").split()
    for item in custom_tags if isinstance(item, dict)
}

# ==================================
# 2. Tabla de tags automáticos
# ==================================
extension_to_tag = {
    # 📄 Documentación / marcado
    ".md": "[[Markdown]]",
    ".rst": "[[Markdown]]",
    ".txt": "[[Markdown]]",
    ".html": "[[HTML]]",
    ".css": "[[CSS]]",
    ".ipynb": "[[Jupyter]]",
    # 💻 Código fuente (modelos de código)
    ".py": "[[Python]]",
    ".js": "[[JavaScript]]",
    ".ts": "[[TypeScript]]",
    ".java": "[[Java]]",
    ".c": "[[C]]",
    ".h": "[[C]]",
    ".cpp": "[[Cpp]]",
    ".hpp": "[[Cpp]]",
    ".go": "[[Go]]",
    ".rb": "[[Ruby]]",
    ".rs": "[[Rust]]",
    ".php": "[[PHP]]",
    ".kt": "[[Kotlin]]",
    ".swift": "[[Swift]]",
    ".sh": "[[Shell]]",
    ".ps1": "[[PowerShell]]",
    ".bat": "[[Batch]]",
    ".pl": "[[Perl]]",
    ".lua": "[[Lua]]",
    ".r": "[[R]]",
    # 🔧 Config / datos
    ".json": "[[JSON]]",
    ".yml": "[[YAML]]",
    ".yaml": "[[YAML]]",
    ".toml": "[[TOML]]",
    ".ini": "[[TOML]]",
    ".csv": "[[CSV]]",
    ".xml": "[[XML]]",
    ".sql": "[[SQL]]",
    # 🐳 Infraestructura
    "Dockerfile": "[[Dockerfile]]",
    "Makefile": "[[Makefile]]",
    # 🧬 Bioinformática
    ".fasta": "[[BioInfo]]",
    ".fastq": "[[BioInfo]]",
    ".vcf": "[[BioInfo]]",
    ".gff": "[[BioInfo]]",
    ".pdb": "[[BioInfo]]",
    # ✨ Contenido simbólico (extensiones hipotéticas)
    ".iching": "[[Modelo Simbólico]]",
}

# Archivos sin extensión con nombre especial
special_name_to_tag = {
    "Dockerfile": "[[Dockerfile]]",
    "Makefile": "[[Makefile]]",
    ".gitignore": "[[Git]]",
}

# ==============================
# 3. Función principal
# ==============================

def get_tags_for_file(file_path: Path) -> List[str]:
    """Devuelve una lista de tags TiddlyWiki para el archivo dado."""

    # 3.1 Primero: buscar en JSON personalizados
    rel_title = "-" + str(file_path.relative_to(Path(__file__).resolve().parents[1])).replace(os.sep, '_')
    if rel_title in TITLE_TO_TAGS:
        return TITLE_TO_TAGS[rel_title]

    # 3.2 Segundo: asignar por nombre especial o extensión
    name = file_path.name
    if name in special_name_to_tag:
        return [special_name_to_tag[name]]

    tag = extension_to_tag.get(file_path.suffix.lower())
    if tag:
        return [tag]

    # 3.3 Fallback
    return ['[[--- 🧬 Por Clasificar]]']

# ------------------------------
if __name__ == "__main__":
    # Pequeño test manual
    import sys
    for f in sys.argv[1:]:
        p = Path(f)
        print(p, "->", get_tags_for_file(p))
