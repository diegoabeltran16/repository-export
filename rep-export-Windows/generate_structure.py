"""
📦 Script: generate_structure.py
📍 Ubicación: scripts/generate_structure.py

🧠 Función:
Este script genera una vista estructurada del proyecto y la guarda como `estructura.txt` en la raíz del repositorio.

Se basa en el comando de Windows `tree /F /A`, que:
- Muestra carpetas y archivos
- Usa solo caracteres ASCII (compatibles con UTF-8)

🎯 Este archivo es utilizado por otros módulos (como `tiddler_exporter.py`)
para detectar cambios estructurales y generar documentación viva.

✅ Cómo ejecutarlo:

    python scripts/generate_structure.py
"""

import subprocess
from pathlib import Path

def generate_structure_file():
    """Genera `estructura.txt` con tree /F /A en codificación UTF-8."""
    root = Path(__file__).resolve().parents[1]
    output_path = root / "estructura.txt"
    comando = f'tree /F /A | Out-File -FilePath "{output_path}" -Encoding utf8'
    subprocess.run(["powershell", "-Command", comando], shell=True)
    print(f"\n📂 Estructura del proyecto exportada a:\n   {output_path}")

# 🚪 Entrada directa
if __name__ == "__main__":
    generate_structure_file()