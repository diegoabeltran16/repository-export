"""
📦 Módulo: tag_mapper.py
🎯 Ubicación: scripts/tag_mapper.py

🧠 Función:
Este módulo se encarga de asignar tags semánticos a archivos del proyecto,
basándose en una fuente centralizada: `OpenPages.json`.

Este JSON contiene entradas del tipo:
{
    "title": "-src_logger.py",
    "tags": "[[--- Codigo]] [[Python]] [[--📘 Documentacion]]"
}

🚀 Este módulo expone una función principal:
    get_tags_for_file(file_path: Path) -> List[str]

Y se puede usar desde:
    - tiddler_exporter.py
    - exploradores semánticos
    - validadores de tags

⚠️ Si el archivo no está en OpenPages.json, retorna:
    ['[[--- 🧬 Por Clasificar]]']
"""

import json
from pathlib import Path
import os


# ========================================
# ⚙️ CONFIGURACIÓN DEL JSON SEMÁNTICO
# ========================================
TIDDLERS_IMPORT_PATH = Path(__file__).resolve().parents[1] / "scripts/tiddlers-import/OpenPages.json"

# ========================================
# 📥 CARGA DEL JSON UNA SOLA VEZ
# ========================================
try:
    with open(TIDDLERS_IMPORT_PATH, 'r', encoding='utf-8') as f:
        tag_data = json.load(f)
except FileNotFoundError:
    print(f"⚠️ No se encontró el archivo OpenPages.json en: {TIDDLERS_IMPORT_PATH}")
    tag_data = []

# Creamos un índice: título → lista de tags
title_to_tags = {}
for item in tag_data:
    title = item.get("title", "").strip()
    tags = item.get("tags", "")
    title_to_tags[title] = tags.split()

# ========================================
# 🔎 FUNCIÓN PRINCIPAL DE CONSULTA
# ========================================
def get_tags_for_file(file_path: Path) -> list[str]:
    """
    Dado un archivo del proyecto, retorna la lista de tags correspondientes
    según el título TiddlyWiki generado (ej. "-src_logger.py").
    Si no se encuentra, retorna [[--- 🧬 Por Clasificar]]
    """
    rel_title = "-" + str(file_path.relative_to(Path(__file__).resolve().parents[1])).replace(os.sep, '_')
    return title_to_tags.get(rel_title, ['[[--- 🧬 Por Clasificar]]'])