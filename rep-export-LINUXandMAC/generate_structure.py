"""
📦 Script: generate_structure.py
📍 Ubicación: rep-export-LINUX/generate_structure.py

🧠 Función:
Este script genera una vista estructurada del proyecto y la guarda como `estructura.txt` en la raíz del repositorio.

Se basa en el comando de Windows `tree /F /A`, que:
- Muestra carpetas y archivos
- Usa solo caracteres ASCII (compatibles con UTF-8)

🎯 Este archivo es utilizado por otros módulos (como `tiddler_exporter.py`)
para detectar cambios estructurales

✅ Cómo ejecutarlo:

    python3 rep-export-LINUX/generate_structure.py
"""

import subprocess
from pathlib import Path

def generate_structure_file():
    """Genera `estructura.txt` con tree -a -F en codificación UTF-8 (Linux)."""
    root = Path(__file__).resolve().parents[1]  # Carpeta raíz del proyecto
    output_path = root / "estructura.txt"

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            subprocess.run(["tree", "-a", "-F"], cwd=root, stdout=f)
        print(f"\n📂 Estructura del proyecto exportada a:\n   {output_path}")
    except FileNotFoundError:
        print("❌ El comando 'tree' no está instalado. Instálalo con:\n   sudo apt install tree")

# 🚪 Entrada directa
if __name__ == "__main__":
    generate_structure_file()
