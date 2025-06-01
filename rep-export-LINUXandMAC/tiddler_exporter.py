"""
📦 Script: tiddler_exporter.py
📍 Ubicación: rep-export-LINUX/tiddler_exporter.py

🧠 Función:
Este script recorre todos los archivos fuente del proyecto, detecta si su contenido ha cambiado,
y si es así, genera un archivo `.json` (un tiddler en formato TiddlyWiki) listo para importar.

🔖 Cada archivo se convierte en un "tiddler", con:
  - Nombre prefijado con `-` (ej: -src_logger.py)
  - Tags semánticos obtenidos desde `OpenPages.json` a través de `tag_mapper.py`
  - Bloque markdown con el contenido del archivo y resaltado según su lenguaje

🎯 Compatible con TiddlyWiki, offline, AI-ready y 100% Python puro.

✅ Cómo ejecutarlo:

    # Exporta solo si hay cambios detectados
    python3 rep-export-LINUX/tiddler_exporter.py

    # Modo simulación (solo imprime qué archivos cambiarían)
    python3 rep-export-LINUX/tiddler_exporter.py --dry-run
"""

import os
import json
import hashlib
import tag_mapper  # Importa la lógica de tags desde scripts/tag_mapper.py
from datetime import datetime, timezone
from pathlib import Path
from typing import List

# ==========================
# ⚙️ CONFIGURACIÓN GENERAL
# ==========================

# __file__ = rep-export-LINUX/tiddler_exporter.py
# ROOT_DIR apunta a la carpeta raíz del repositorio (dos niveles arriba de este script)
ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "tiddlers-export"  # Carpeta donde se escribirán los tiddlers JSON
HASH_FILE = SCRIPT_DIR / ".hashes.json"       # Archivo que almacena hashes previos para detectar cambios

# Extensiones válidas (archivos que queremos convertir a tiddlers)
VALID_EXTENSIONS = ['.py', '.md', '.json', '.sh', '.html', '.css', '.yml', '.txt','.go']
# Archivos sin extensión que queremos incluir (ej. .gitignore)
ALLOWED_FILENAMES = ['.gitignore']

# Carpetas que NO queremos recorrer (ignorar)
IGNORE_DIRS = [
    '__pycache__', 'venv', '.venv', 'dist', 'node_modules', 'output', 'input',
    '.pytest_cache', 'configs', 'media', 'project_details', 'tiddlers-export'
]

# Mapa para determinar el lenguaje de resaltado al generar el bloque markdown
LANGUAGE_MAP = {
    '.py': 'python',
    '.md': 'markdown',
    '.json': 'json',
    '.sh': 'bash',
    '.yml': 'bash',
    '.html': 'html',
    '.txt': 'txt',
    '.css': 'css',
    '.go' : 'go'
}

# Mapa para archivos especiales por nombre (ej. .gitignore)
SPECIAL_LANGUAGES = {
    '.gitignore': 'gitignore'
}

# ==============================
# 🔎 FUNCIONES AUXILIARES
# ==============================

def get_all_files(directory: Path) -> List[Path]:
    """
    Recorre recursivamente 'directory' y devuelve una lista de Path
    solo con archivos válidos (según VALID_EXTENSIONS o ALLOWED_FILENAMES),
    saltando carpetas definidas en IGNORE_DIRS.
    """
    all_files: List[Path] = []
    for root, dirs, files in os.walk(directory):
        # Filtramos directorios ignorados
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for filename in files:
            ext = Path(filename).suffix
            if ext in VALID_EXTENSIONS or filename in ALLOWED_FILENAMES:
                all_files.append(Path(root) / filename)
    return all_files

def get_hash(content: str) -> str:
    """
    Recibe una cadena ("content") y retorna su hash SHA-1 en hexadecimal.
    Se usa para detectar cambios en el contenido de archivos.
    """
    return hashlib.sha1(content.encode('utf-8')).hexdigest()

def safe_title(path: Path) -> str:
    """
    Dado un Path absoluto o relativo dentro de ROOT_DIR,
    retorna un título válido para un tiddler:
      - Prefijo "-" (para cumplir con convención TiddlyWiki).
      - Reemplazo de separadores por guión bajo.
    Ejemplo: si 'path' es /repo/src/utils/helpers.py,
    y ROOT_DIR = /repo, title será "-src_utils_helpers.py"
    """
    return '-' + str(path.relative_to(ROOT_DIR)).replace(os.sep, '_')

def detect_language(file_path: Path) -> str:
    """
    Determina el lenguaje para el bloque de código en markdown:
      - Si el nombre del archivo está en SPECIAL_LANGUAGES, lo retorna.
      - En otro caso, busca la extensión en LANGUAGE_MAP.
      - Si no lo encuentra, usa "text" por defecto.
    """
    name = file_path.name
    if name in SPECIAL_LANGUAGES:
        return SPECIAL_LANGUAGES[name]
    ext = file_path.suffix
    return LANGUAGE_MAP.get(ext, 'text')

# ==============================
# 🚀 EXPORTADOR PRINCIPAL
# ==============================

def export_tiddlers(dry_run: bool = False):
    """
    Recorre todos los archivos válidos en ROOT_DIR, calcula su hash y
    comprueba si ha cambiado desde la última ejecución (almacenada en .hashes.json).

    Para cada archivo que cambió:
      1. Genera un "title" válido con safe_title().
      2. Obtiene sus tags usando tag_mapper.get_tags_for_file().
      3. Construye el contenido markdown del tiddler (con bloque de código).
      4. Escribe un JSON de tiddler en OUTPUT_DIR (salvo que sea dry_run).
      5. Actualiza la lista de archivos modificados.

    Parámetros:
    - dry_run: Si es True, solo imprime qué archivos cambiarían, sin escribir nada.
    """
    # Asegurarse de que OUTPUT_DIR existe
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Cargar hashes anteriores (si existe .hashes.json); sino, empezar con dict vacío
    if HASH_FILE.exists():
        try:
            with open(HASH_FILE, 'r', encoding='utf-8') as f:
                old_hashes = json.load(f)
        except Exception:
            print(f"⚠️ No se pudo leer {HASH_FILE}. Se re-iniciarán todos los hashes.")
            old_hashes = {}
    else:
        old_hashes = {}

    new_hashes: dict[str, str] = {}
    changed_files: List[str] = []

    # Recorrer cada archivo válido en el repositorio
    for file_path in get_all_files(ROOT_DIR):
        # Ruta relativa como string (ej: "src/utils/helpers.py")
        rel_path = str(file_path.relative_to(ROOT_DIR))

        # Detectar lenguaje para resaltar código en markdown
        lang = detect_language(file_path)

        # Leer contenido del archivo
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"⚠️ Error leyendo {rel_path}: {e}")
            # Si no pudo leer, saltar este archivo
            continue

        # Calcular hash SHA1 del contenido
        hash_now = get_hash(content)
        new_hashes[rel_path] = hash_now

        # Si el hash coincide con el anterior, no hubo cambios → saltar
        if old_hashes.get(rel_path) == hash_now:
            continue

        # ---------- Ha habido cambio (o es primera vez) ----------
        # 1) Construir título
        title = safe_title(file_path)

        # 2) Obtener tags semánticos (o tag por defecto si no existe JSON)
        tags_list = tag_mapper.get_tags_for_file(file_path)
        tags_joined = ' '.join(tags_list)

        # 3) Construir bloque de texto Markdown para el tiddler
        #    - Encabezado con sección Tags
        #    - Luego bloque de código con el contenido real
        text_block = (
            "## [[Tags]]\n"
            f"{tags_joined}\n\n"
            f"```{lang}\n"
            f"{content}\n"
            "```"
        )

        # 4) Crear estructura JSON del tiddler
        tiddler = {
            "title": title,
            "text": text_block,
            "tags": tags_joined,
            "type": "text/markdown",
            # Fechas en formato TiddlyWiki: YYYYMMDDhhmmssSSS (milisegundos)
            "created": datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:17],
            "modified": datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:17],
        }

        # Si estamos en modo simulación, imprimimos y saltamos escritura
        if dry_run:
            print(f"[dry-run] Detectado cambio en: {rel_path}")
            continue

        # 5) Escribir archivo JSON dentro de OUTPUT_DIR
        out_file = OUTPUT_DIR / f"{title}.json"
        try:
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump(tiddler, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ No se pudo escribir {out_file}: {e}")
            continue

        # Agregar a la lista de archivos modificados (para reportar al final)
        changed_files.append(rel_path)

    # ======= Actualizar archivo de hashes si no es dry_run =======
    if not dry_run:
        try:
            with open(HASH_FILE, 'w', encoding='utf-8') as f:
                json.dump(new_hashes, f, indent=2)
        except Exception as e:
            print(f"⚠️ No se pudo actualizar {HASH_FILE}: {e}")

    # ======= Informe final =======
    print(f"\n📦 Archivos modificados: {len(changed_files)}")
    if changed_files:
        for path in changed_files:
            print(f"  ✅ Exportado: {path}")
    else:
        print("  🔁 Sin cambios detectados.")
        

# ==============================
# 🧪 CLI: Entrada directa
# ==============================
if __name__ == "__main__":
    import sys
    # Detectar bandera --dry-run
    dry = '--dry-run' in sys.argv
    export_tiddlers(dry_run=dry)
