"""
📦 Módulo: tag_mapper.py
🎯 Ubicación esperada: rep-export-LINUX/tag_mapper.py

🧠 Función:
Este módulo se encarga de asignar tags semánticos a archivos del proyecto,
basándose en uno o varios archivos JSON alojados dentro de `tiddler_tag_doc/`.
Cualquiera que sea el nombre del JSON, si termina en `.json` dentro de la carpeta,
se cargará y se añadirá a la lista de entradas semánticas.

✨ Comportamiento:
  - Busca la carpeta `tiddler_tag_doc/` en el mismo nivel de este script.
  - Recorre todos los archivos `*.json` dentro de esa carpeta.
  - Si la carpeta no existe o no hay JSON, emite un aviso pero continúa sin tags personalizados.
  - Si un JSON está mal formado, emite un aviso y lo omite, pero carga los demás.
  - Crea un índice global (clave: "title", valor: lista de tags) combinando todos los JSON válidos.
  - Si un archivo no se encuentra en el índice final, retorna `['[[--- 🧬 Por Clasificar]]']`.
"""

import json
from pathlib import Path
import os

# ===================================
# ⚙️ CONFIGURACIÓN: ruta a la carpeta
# ===================================
# Asumimos que este script está en rep-export-LINUX/tag_mapper.py,
# por lo que el directorio "tiddler_tag_doc" está en el mismo nivel que este archivo.
TIDDLER_TAG_DIR = Path(__file__).resolve().parents[0] / "tiddler_tag_doc"

# =====================================
# 📥 CARGA DE TODOS LOS JSON EN tiddler_tag_doc
# =====================================
tag_data = []  # Acá acumularemos todas las entradas de JSON

if TIDDLER_TAG_DIR.exists() and TIDDLER_TAG_DIR.is_dir():
    # Buscamos todos los archivos con extensión .json en orden alfabético
    json_files = sorted(TIDDLER_TAG_DIR.glob("*.json"))
    if not json_files:
        print(f"⚠️ No se encontraron archivos .json en: {TIDDLER_TAG_DIR}")
    else:
        for json_path in json_files:
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        # Si el JSON es una lista de objetos, lo agregamos
                        tag_data.extend(data)
                    else:
                        print(f"⚠️ El contenido de '{json_path.name}' no es una lista JSON válida. Se omitirá.")
            except json.JSONDecodeError:
                print(f"⚠️ El archivo existe pero no es un JSON válido: {json_path}")
            except Exception as e:
                print(f"⚠️ Error al leer '{json_path.name}': {e}")
else:
    print(f"⚠️ No se encontró la carpeta tiddler_tag_doc en: {TIDDLER_TAG_DIR}")

# ============================================================
# 📑 Construir índice global: título (string) → lista de tags
# ============================================================
# Cada objeto en tag_data debería tener al menos:
#   { "title": "-ruta_relativa_al_archivo", "tags": "[[TagA]] [[TagB]]" }
# Si no cumple, simplemente lo saltamos.
title_to_tags: dict[str, list[str]] = {}

for item in tag_data:
    if not isinstance(item, dict):
        continue  # saltamos cualquier cosa que no sea un dict
    title = item.get("title", "").strip()
    tags_str = item.get("tags", "")
    if title and isinstance(tags_str, str):
        # Convertimos la cadena de tags en lista
        tags_list = tags_str.split()
        title_to_tags[title] = tags_list

# ================================================================
# 🔎 FUNCIÓN PRINCIPAL: obtener lista de tags para un archivo dado
# ================================================================
def get_tags_for_file(file_path: Path) -> list[str]:
    """
    Dado un Path absoluto (o relativo) de un archivo dentro del repo,
    construye el 'título' (matching con los JSON) y retorna la lista de tags.
    Si no lo encuentra en el índice, retorna ['[[--- 🧬 Por Clasificar]]'].

    Ejemplo de construcción de título:
      Si file_path = /.../src/utils/helpers.py
      y el ROOT (para el índice) es un nivel arriba de este script,
      entonces rel_title = "-src_utils_helpers.py"

    Parámetros:
    - file_path: Path hacia el archivo real en el repositorio.

    Retorna:
    - List[str]: lista de tags (p.ej. ["[[TagA]]", "[[TagB]]"]) o
                 ['[[--- 🧬 Por Clasificar]]'] si no existe.
    """
    try:
        # Determinar carpeta raíz del repo (dos niveles arriba de este script)
        root_dir = Path(__file__).resolve().parents[1]
        rel_path_unix = str(file_path.relative_to(root_dir)).replace(os.sep, '_')
        rel_title = "-" + rel_path_unix
    except Exception:
        # Si no se puede calcular la ruta relativa, asignamos prefijo por defecto
        rel_title = "-" + file_path.name

    # Devolvemos los tags si existen en el índice, o el fallback si no
    return title_to_tags.get(rel_title, ['[[--- 🧬 Por Clasificar]]'])
