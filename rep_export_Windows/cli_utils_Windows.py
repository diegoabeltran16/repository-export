#!/usr/bin/env python3
"""
Módulo: cli_utils.py
Ubicación: rep-export-Windows/

Utilidades comunes para scripts CLI:
- `prompt_yes_no`  → Preguntas sí/no con valor por defecto.
- `run_cmd`        → Ejecutar subprocesos con captura de stdout, stderr y código.
- `get_additional_args` → Parsear argumentos libres del usuario.
- `confirm_overwrite`   → Confirmar sobreescritura de archivos existentes.
- `safe_print`     → Imprime mensajes evitando errores de codificación (emojis).
- `load_ignore_spec` → Carga y compila patrones de `.gitignore`.
- `is_ignored`     → Verifica si una ruta debe ser ignorada según `.gitignore`.
"""
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Optional
from pathspec import PathSpec


def safe_print(message: str) -> None:
    """Imprime evitando errores de codificación en consolas con encoding limitado."""
    try:
        print(message)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or 'utf-8'
        filtered = message.encode(encoding, errors='ignore').decode(encoding)
        print(filtered)


def prompt_yes_no(question: str, default: bool = False) -> bool:
    """Pregunta interactiva sí/no con valor por defecto."""
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
    Ejecuta un comando externo y captura salida.

    Returns:
        exit_code: Código de salida del proceso
        stdout:   Salida estándar capturada
        stderr:   Salida de error capturada
    """
    safe_print(f"\n▶️ Ejecutando: {' '.join(cmd)}\n")
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    for line in process.stdout:
        print(line, end='')  # Muestra cada línea en tiempo real
    process.wait()
    return process.returncode, None, None


def get_additional_args(script_name: str) -> List[str]:
    """Solicita argumentos adicionales para un script (retorna lista)."""
    extras = input(f"Argumentos extra para {script_name} (separados por espacios), o Enter para ninguno: ").strip()
    return extras.split() if extras else []


def confirm_overwrite(path: Path) -> bool:
    """Verifica si el usuario acepta sobrescribir el archivo si ya existe."""
    if path.exists():
        return prompt_yes_no(f"El archivo '{path.name}' ya existe. ¿Sobrescribir?", default=False)
    return True


def load_ignore_spec(repo_root: Path):
    """
    Carga y compila los patrones de `.gitignore` desde el directorio raíz.
    Devuelve un PathSpec usable para match_file(path).
    """
    gitignore = repo_root / '.gitignore'
    if not gitignore.is_file():
        return None
    lines = [
        ln.strip() for ln in gitignore.read_text(encoding='utf-8').splitlines()
        if ln.strip() and not ln.strip().startswith('#')
    ]
    if not lines:
        return None
    return PathSpec.from_lines('gitwildmatch', lines)


def is_ignored(path: Path, ignore_spec):
    """
    Verifica si una ruta debe ser ignorada por `.gitignore`.
    Path debe ser relativo o absoluto dentro de repo_root.
    """
    if ignore_spec is None:
        return False
    rel = str(path)
    return ignore_spec.match_file(rel)


def alguna_funcion():
    from tag_mapper_windows import get_tags_for_file
    # ...usa get_tags_for_file aquí...
