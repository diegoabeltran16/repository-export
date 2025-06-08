#!/usr/bin/env python3
"""
Módulo: cli_utils.py
Ubicación: rep-export-LINUXandMAC/

Utilidades comunes para scripts CLI de Linux/macOS:
- `safe_print`         → Imprime mensajes evitando errores de codificación (útil para emojis).
- `prompt_yes_no`      → Preguntas interactivas Sí/No con valor por defecto.
- `run_cmd`            → Ejecutar comandos externos capturando stdout, stderr y código de salida.
- `get_additional_args`→ Parsear argumentos libres introducidos por el usuario.
- `confirm_overwrite`  → Confirmar sobrescritura de archivos existentes.
"""
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Optional


def safe_print(message: str) -> None:
    """Imprime cadena sin fallar si la consola no soporta algunos caracteres."""
    try:
        print(message)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or 'utf-8'
        filtered = message.encode(encoding, errors='ignore').decode(encoding)
        print(filtered)


def prompt_yes_no(question: str, default: bool = False) -> bool:
    """Pregunta interactiva Sí/No con valor por defecto."""
    default_str = 'S/n' if default else 's/N'
    while True:
        resp = input(f"{question} [{default_str}]: ").strip().lower()
        if not resp:
            return default
        if resp in ('s', 'si', 'y', 'yes'):
            return True
        if resp in ('n', 'no'):
            return False
        safe_print("❗ Respuesta inválida. Usa 's' o 'n'.")


def run_cmd(cmd: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """
    Ejecuta un comando externo y retorna (exit_code, stdout, stderr).
    """
    safe_print(f"\n▶️ Ejecutando: {' '.join(cmd)}\n")
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = proc.communicate()
    if out:
        safe_print(out)
    if proc.returncode != 0:
        safe_print(f"❌ Error (code {proc.returncode}) al ejecutar: {cmd[0]}")
        if err:
            safe_print(f"📋 stderr:\n{err}")
    return proc.returncode, out, err


def get_additional_args(script_name: str) -> List[str]:
    """Solicita al usuario argumentos adicionales para un script CLI."""
    extras = input(f"Argumentos extra para {script_name} (separados por espacios), o Enter para ninguno: ").strip()
    return extras.split() if extras else []


def confirm_overwrite(path: Path) -> bool:
    """Si `path` existe, pregunta si el usuario desea sobrescribirlo."""
    if path.exists():
        return prompt_yes_no(f"El archivo '{path.name}' ya existe. ¿Sobrescribir?", default=False)
    return True
