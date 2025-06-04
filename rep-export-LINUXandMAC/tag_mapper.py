#!/usr/bin/env python3
"""
📦 Módulo: tag_mapper.py
🎯 Plataforma: Linux / macOS

Función:
Este módulo se encarga de asignar tags semánticos a cada archivo de un repositorio.
Primero intenta cargar tags personalizados desde archivos JSON en `tiddler_tag_doc/`.
Si no hay un tag personalizado para el archivo, asigna un tag basado en el tipo de archivo (extensión).

Salida:
- Lista de tags en formato TiddlyWiki (`[[TagName]]`).
"""
import json
from pathlib import Path
import os

# ========================================
# ⚙️ CONFIGURACIÓN: ruta a la carpeta de JSON de tags
# ========================================
TIDDLER_TAG_DIR = Path(__file__).resolve().parents[0] / "tiddler_tag_doc"

# Carga todos los JSON en la carpeta para construir un índice título→tags
title_to_tags = {}

if TIDDLER_TAG_DIR.exists() and TIDDLER_TAG_DIR.is_dir():
    for json_path in sorted(TIDDLER_TAG_DIR.glob("*.json")):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        title = item.get("title", "").strip()
                        tags_str = item.get("tags", "").strip()
                        if title and isinstance(tags_str, str):
                            # Convertir cadena de tags en lista: asume sintaxis [[Tag]]
                            tags_list = tags_str.split()
                            title_to_tags[title] = tags_list
        except json.JSONDecodeError:
            print(f"⚠️ JSON inválido en: {json_path.name}, se omite.")
        except Exception as e:
            print(f"⚠️ Error al leer '{json_path.name}': {e}")
else:
    # Si no existe la carpeta, no hay tags personalizados
    pass

# ========================================
# 🗂️ Mapeo de extensiones a nombres de tags
# ========================================
EXTENSION_TAG_MAP = {
    '.py': 'Python',
    '.md': 'Markdown',
    '.json': 'JSON',
    '.sh': 'Shell',
    '.bash': 'Shell',
    '.yml': 'YAML',
    '.yaml': 'YAML',
    '.html': 'HTML',
    '.htm': 'HTML',
    '.css': 'CSS',
    '.go': 'Go',
    '.js': 'JavaScript',
    '.ts': 'TypeScript',
    '.java': 'Java',
    '.c': 'C',
    '.cpp': 'C++',
    '.cc': 'C++',
    '.hpp': 'C++',
    '.h': 'C/C++ Header',
    '.rs': 'Rust',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.kt': 'Kotlin',
    '.kts': 'Kotlin',
    '.swift': 'Swift',
    '.xml': 'XML',
    '.sql': 'SQL',
    '.toml': 'TOML',
    '.csv': 'CSV',
    '.pl': 'Perl',
    '.lua': 'Lua',
    '.ps1': 'PowerShell',
    '.bat': 'Batch',
    '.dockerfile': 'Dockerfile',
    '.makefile': 'Makefile',
    '.tex': 'LaTeX',
    '.rst': 'reStructuredText',
    '.cfg': 'Config',
    '.ini': 'Config',
    '.log': 'Log',
    '.txt': 'Text'
}

# Algunos archivos sin extensión específica tienen nombres propios
SPECIAL_FILENAMES = {
    'Dockerfile': 'Dockerfile',
    'Makefile': 'Makefile',
    'README': 'README',
    'LICENSE': 'License'
}

# Etiqueta por defecto cuando no se reconoce el tipo
DEFAULT_TAG = 'Unknown'

# ========================================
# 🔎 FUNCIÓN PRINCIPAL: obtener lista de tags
# ========================================

def get_tags_for_file(file_path: Path) -> list[str]:
    """
    Dado un Path de archivo dentro del repositorio, retorna lista de tags.
    - Primero: intenta encontrar en el índice `title_to_tags` (JSON definidos).
    - Si no existe, deriva un tag basado en la extensión o nombre de archivo.

    Retorna:
    - List[str]: lista de tags en formato `[[TagName]]`.
    """
    # Construir la clave de título en formato TiddlyWiki: prefijo '-' y slashes reemplazados
    try:
        root_dir = Path(__file__).resolve().parents[1]
        rel_path = str(file_path.relative_to(root_dir)).replace(os.sep, '_')
        title = '-' + rel_path
    except Exception:
        # Si falla, usar solo el nombre de archivo
        title = '-' + file_path.name

    # 1) Verificar tags personalizados
    if title in title_to_tags:
        return title_to_tags[title]

    # 2) Derivar tag por extensión
    name = file_path.name
    ext = file_path.suffix.lower()

    # Revisar archivos con nombre especial (sin extensión)
    if name in SPECIAL_FILENAMES:
        tag_name = SPECIAL_FILENAMES[name]
    # Revisar mapeo por extensión
    elif ext in EXTENSION_TAG_MAP:
        tag_name = EXTENSION_TAG_MAP[ext]
    else:
        tag_name = DEFAULT_TAG

    # Formatear como tag TiddlyWiki
    return [f"[[{tag_name}]]"]

# Permitir uso del módulo como script para pruebas
if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Uso: python tag_mapper.py <ruta_archivo>")
        sys.exit(1)
    fp = Path(sys.argv[1])
    tags = get_tags_for_file(fp)
    print(f"Archivo: {fp} → Tags: {tags}")
