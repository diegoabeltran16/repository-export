#!/usr/bin/env python3
"""
📦 Módulo: tag_mapper.py
🎯 Plataforma: Windows

Función:
Este módulo asigna tags semánticos a cada archivo del repositorio para generar tiddlers.

1. Busca archivos JSON en la carpeta `tiddler_tag_doc/` (ubicada al mismo nivel que este script).
   - Cada JSON debe contener una lista de objetos con campos:
     {
       "title": "-ruta_relativa_al_archivo",
       "tags": "[[Tag1]] [[Tag2]]"
     }
2. Construye un índice global `title -> tags` combinando todos los JSON válidos.
3. Cuando se requiere un tag para un archivo:
   a) Se construye el título TiddlyWiki (prefijo `-` + ruta relativa con `_`).
   b) Si existe en el índice, retorna los tags personalizados.
   c) Si no existe, asigna un tag basado en la extensión o nombre de archivo.
   d) Si la extensión o nombre no está en el mapeo, retorna `['[[--- 🧬 Por Clasificar]]']`.

Formato de tags: `[[TagName]]`.
"""
import json
from pathlib import Path
import os

# ========================
# 📁 CONFIGURACIÓN
# ========================
# Carpeta donde se buscan JSON de tags personalizados (al mismo nivel que este script)
TIDDLER_TAG_DIR = Path(__file__).resolve().parents[0] / "tiddler_tag_doc"

# Nombre de JSON central personalizado (antiguamente OpenPages.json)
# Pero ahora cargamos todos los JSON en tiddler_tag_doc/

# Diccionario de extensiones a Tag por defecto
EXTENSION_TO_TAG = {
    '.py': 'Python',
    '.md': 'Markdown',
    '.json': 'JSON',
    '.sh': 'Shell',
    '.bat': 'Batch',
    '.ps1': 'PowerShell',
    '.yml': 'YAML',
    '.yaml': 'YAML',
    '.html': 'HTML',
    '.css': 'CSS',
    '.js': 'JavaScript',
    '.jsx': 'JavaScript',
    '.ts': 'TypeScript',
    '.tsx': 'TypeScript',
    '.java': 'Java',
    '.c': 'C',
    '.cpp': 'C++',
    '.cc': 'C++',
    '.h': 'C/C++ Header',
    '.hpp': 'C++ Header',
    '.cs': 'C#',
    '.rb': 'Ruby',
    '.go': 'Go',
    '.rs': 'Rust',
    '.php': 'PHP',
    '.pl': 'Perl',
    '.lua': 'Lua',
    '.kt': 'Kotlin',
    '.kts': 'Kotlin',
    '.swift': 'Swift',
    '.xml': 'XML',
    '.sql': 'SQL',
    '.toml': 'TOML',
    '.csv': 'CSV',
    '.ini': 'INI',
    '.cfg': 'CFG',
    '.dockerfile': 'Dockerfile',
    'makefile': 'Makefile',
    'LICENSE': 'License',
    'README': 'Markdown'
}

# Fallback tag cuando no se reconoce extensión ni hay tag personalizado
DEFAULT_TAG = '--- 🧬 Por Clasificar'

# ========================================
# 📥 CARGA DE TAGS PERSONALIZADOS
# ========================================

tag_data = []  # lista de diccionarios cargados desde JSON

if TIDDLER_TAG_DIR.exists() and TIDDLER_TAG_DIR.is_dir():
    json_files = sorted(TIDDLER_TAG_DIR.glob("*.json"))
    for json_path in json_files:
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    tag_data.extend(data)
                else:
                    print(f"⚠️ El contenido de '{json_path.name}' no es una lista JSON válida. Se omitirá.")
        except json.JSONDecodeError:
            print(f"⚠️ JSON mal formado: {json_path.name}. Se omitirá.")
        except Exception as e:
            print(f"⚠️ Error al leer '{json_path.name}': {e}")
else:
    # Si la carpeta no existe, no es error; se usan solo tags por extensión
    pass

# Construir índice de título -> lista de tags
TITLE_TO_TAGS = {}
for item in tag_data:
    if not isinstance(item, dict):
        continue
    title = item.get("title", "").strip()
    tags_str = item.get("tags", "").strip()
    if title and isinstance(tags_str, str):
        tags_list = tags_str.split()
        TITLE_TO_TAGS[title] = tags_list

# ========================================
# 🔎 FUNCIÓN PRINCIPAL
# ========================================

def get_tags_for_file(file_path: Path) -> list[str]:
    """
    Dado un Path de archivo, retorna la lista de tags.
    - Construye el título TiddlyWiki: '-' + ruta relative con '_' en lugar de os.sep.
    - Si existe en TITLE_TO_TAGS, retorna esa lista.
    - Sino, busca en EXTENSION_TO_TAG o nombres especiales.
    - Si no reconoce, retorna [DEFAULT_TAG].
    """
    try:
        root_dir = Path(__file__).resolve().parents[1]
        rel_path_unix = str(file_path.relative_to(root_dir)).replace(os.sep, '_')
        rel_title = '-' + rel_path_unix
    except Exception:
        rel_title = '-' + file_path.name

    # 1) Tags personalizados
    if rel_title in TITLE_TO_TAGS:
        return TITLE_TO_TAGS[rel_title]

    # 2) Tag basado en extensión o nombre
    name = file_path.name
    ext = file_path.suffix.lower()
    if ext in EXTENSION_TO_TAG:
        return [f"[[{EXTENSION_TO_TAG[ext]}]]"]

    # 3) Si el archivo coincide por nombre exacto (sin extensión)
    base = file_path.name.lower()
    if base in EXTENSION_TO_TAG:
        return [f"[[{EXTENSION_TO_TAG[base]}]]"]

    # 4) Si el nombre del archivo contiene una clave (p. ej. 'Makefile', 'Dockerfile')
    lower_name = file_path.name.lower()
    for key in ['makefile', 'dockerfile', 'readme', 'license']:
        if key in lower_name:
            tag = EXTENSION_TO_TAG.get(key)
            if tag:
                return [f"[[{tag}]]"]

    # 5) Fallback
    return [f"[[{DEFAULT_TAG}]]"]

