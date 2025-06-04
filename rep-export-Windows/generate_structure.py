"""
📦 Script: generate_structure_windows.py
🖥️ Plataforma: Windows (PowerShell/Command Prompt)

Objetivo
========
Generar `estructura.txt` en la raíz del repositorio con una representación
ASCII del árbol de carpetas y archivos, **codificado en UTF‑8**, con detección
de dependencias y manejo robusto de errores.

Mejoras sobre la versión original
--------------------------------
1. **Detección de PowerShell y fallback a cmd.exe**
2. **Verificación de la presencia del comando *tree***
3. **`subprocess.run(..., check=True)`** para propagar códigos de error.
4. **Manejo explícito de excepciones** (`FileNotFoundError`,
   `subprocess.CalledProcessError`).
5. **Mensajes de diagnóstico coherentes** para el usuario.
6. **Uso de rutas seguras** (`Path` → cadena con comillas dobles escapadas).

Requisitos
----------
* Windows 10 o superior (o Windows Server).
* Python 3.8+.

Uso
---
```powershell
python generate_structure_windows.py
```
Añade la ruta al `PATH` si decides moverlo a otra carpeta.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence, Optional

# ----------------------------
# 🛠️  Funciones auxiliares
# ----------------------------


def _find_powershell() -> Optional[str]:
    """Devuelve la ruta a *powershell.exe* o *pwsh*, o *None* si no existe."""
    return shutil.which("powershell") or shutil.which("pwsh")


def _build_command(out_path: Path) -> tuple[Sequence[str], bool]:
    """Construye el comando adecuado y devuelve `(cmd, shell)`.

    * Si hay PowerShell disponible se usa `Out-File` (UTF‑8).
    * En caso contrario se hace *fallback* a `cmd.exe /c tree`.
    """
    out_quoted = f"\"{out_path}\""  # comillas dobles para rutas con espacios

    powershell = _find_powershell()
    if powershell:
        # Nota: `-NoProfile` acelera y evita scripts no confiables
        cmd = [
            powershell,
            "-NoProfile",
            "-Command",
            f"tree /F /A | Out-File -FilePath {out_quoted} -Encoding utf8",
        ]
        return cmd, False  # shell innecesario

    # --- Fallback a cmd.exe -------------------------------------------------
    if shutil.which("cmd") is None:
        raise FileNotFoundError(
            "No se encontró PowerShell ni cmd.exe en el sistema; no es posible ejecutar 'tree'."
        )

    cmd = [
        "cmd",
        "/c",
        f"tree /F /A > {out_quoted}"
    ]
    return cmd, False


# ----------------------------
# 🚀 Función principal
# ----------------------------


def generate_structure_file() -> None:
    """Genera `estructura.txt` con salida UTF‑8, manejando errores de forma explícita."""
    root_dir = Path(__file__).resolve().parents[1]
    out_path = root_dir / "estructura.txt"

    # Asegurarse de que el comando *tree* está disponible (es interno, pero puede faltar)
    if shutil.which("tree") is None:
        print(
            "❌ El comando 'tree' no está disponible en el sistema. "
            "Instálalo con Winget (winget install gnuwin32.tree) o añade una alternativa compatible."
        )
        sys.exit(1)

    cmd, use_shell = _build_command(out_path)

    try:
        subprocess.run(cmd, cwd=root_dir, check=True, shell=use_shell)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print("❌ Error al ejecutar el comando para generar la estructura:")
        print(f"   {exc}")
        sys.exit(1)

    print("\n📂 Estructura del proyecto exportada a:")
    print(f"   {out_path}")


# ----------------------------
# 🏁 Entrada directa
# ----------------------------

if __name__ == "__main__":
    generate_structure_file()
