#!/usr/bin/env python3
"""
Asistente interactivo: export_structure_wrapper_windows.py
Ubicación: rep-export-Windows/scripts/

Este script te guía paso a paso para generar un árbol ASCII de tu proyecto en Windows.
Explica las opciones sin tecnicismos y ejecuta `generate_structure.py` con tus parámetros.
"""
import subprocess
import sys
from pathlib import Path


def prompt_yes_no(question: str, default: bool = False) -> bool:
    """Pregunta sí/no al usuario con default."""
    default_str = 'S/n' if default else 's/N'
    while True:
        resp = input(f"{question} [{default_str}]: ").strip().lower()
        if not resp:
            return default
        if resp in ('s', 'si', 'y', 'yes'):
            return True
        if resp in ('n', 'no'):
            return False
        print("Por favor responde 's' o 'n'.")


def main():
    print("\n¡Bienvenido al asistente de generación de estructura para Windows!\n")
    print("Este asistente te ayudará a crear un archivo de texto con el árbol de carpetas y archivos de tu proyecto.")
    print("Opciones disponibles:")
    print("  • Excluir archivos/carpetas sensibles (por defecto)")
    print("  • Respetar patrones de .gitignore")
    print("  • Patrón adicional de exclusión")
    print("  • Elegir nombre de archivo de salida\n")

    # Ruta al script principal
    base = Path(__file__).resolve().parent.parent
    script = base / 'generate_structure.py'
    if not script.exists():
        print(f"❌ No encontré generate_structure.py en {script}")
        sys.exit(1)

    # Preguntas al usuario
    honor_gitignore = prompt_yes_no("¿Deseas respetar las reglas de .gitignore?", default=False)
    patterns_input = input("Ingresa patrones a excluir separados por comas (p.ej.: node_modules,*.log), o Enter para ninguno: ").strip()
    exclude_args = []
    if patterns_input:
        for pat in [p.strip() for p in patterns_input.split(',') if p.strip()]:
            exclude_args.extend(['-e', pat])

    # Archivo de salida
    default_name = 'estructura.txt'
    output_name = input(f"Nombre del archivo de salida [por defecto: {default_name}]: ").strip()
    if not output_name:
        output_name = default_name
    output_args = ['--output', output_name]

    # Construir comando
    cmd = [sys.executable, str(script)]
    if honor_gitignore:
        cmd.append('--honor-gitignore')
    cmd += exclude_args
    cmd += output_args

    # Ejecutar
    print(f"\nEjecutando: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=base)
    if result.returncode == 0:
        print(f"\n✅ ¡Listo! Estructura guardada en '{output_name}'")
    else:
        print("\n❌ Ocurrió un error al generar la estructura. Revisa la salida previa.")
        sys.exit(result.returncode)

if __name__ == '__main__':
    main()
