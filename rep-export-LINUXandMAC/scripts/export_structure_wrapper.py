#!/usr/bin/env python3
"""
Script interactivo: export_structure_wrapper.py
Ubicación: rep-export-LINUXandMAC/scripts/

Este script es un asistente amigable para generar la estructura de tu proyecto.
Hace preguntas sencillas y luego invoca el script principal `generate_structure.py`.
"""
import subprocess
import sys
from pathlib import Path

def prompt_yes_no(question: str, default: bool = True) -> bool:
    yes = 'S' if default else 's'
    no = 'n' if default else 'N'
    prompt = f"{question} [{yes}/{no}]: "
    while True:
        resp = input(prompt).strip().lower()
        if not resp:
            return default
        if resp in ('s', 'si', 'y', 'yes'):
            return True
        if resp in ('n', 'no'):
            return False
        print("Por favor responde 'S' o 'n'.")

def main():
    print("\n¡Bienvenido al asistente de generación de estructura!\n")
    print("Este asistente te ayudará a crear un listado filtrado de carpetas y archivos de tu proyecto.")
    print("Puedes:")
    print("  - Ver una vista previa sin guardar (dry-run)")
    print("  - Generar un archivo de texto con la estructura")
    print("  - Excluir elementos según .gitignore o patrones personalizados\n")

    # Rutas
    base = Path(__file__).resolve().parent.parent
    script = base / 'generate_structure.py'
    if not script.exists():
        print(f"❌ No encontré generate_structure.py en {script}")
        sys.exit(1)

    # Opciones
    dry_run = prompt_yes_no("¿Quieres una vista previa (dry-run)?", default=True)
    honor_gitignore = prompt_yes_no("¿Respetar .gitignore?", default=False)
    custom_patterns = input("Ingresa patrones a excluir separados por comas, o Enter para ninguno: ").strip()
    exclude_args = []
    if custom_patterns:
        for pat in [p.strip() for p in custom_patterns.split(',') if p.strip()]:
            exclude_args.extend(['-e', pat])

    # Salida
    print("\n¿Dónde quieres que se guarde la salida?")
    print("  1) Solo mostrar en pantalla")
    print("  2) Guardar en 'estructura.txt'")
    print("  3) Guardar en nombre personalizado")
    choice = input("Selecciona una opción [1/2/3]: ").strip()
    if choice == '3':
        filename = input("Nombre de archivo (ej: mi_estructura.txt): ").strip()
        output_args = ['--output', filename]
    elif choice == '2':
        output_args = []
    else:
        # para solo mostrar, forzamos dry-run
        if not dry_run:
            dry_run = True
        output_args = []

    # Construir comando
    cmd = [sys.executable, str(script)]
    if dry_run:
        cmd.append('--dry-run')
    if honor_gitignore:
        cmd.append('--honor-gitignore')
    cmd += exclude_args
    cmd += output_args

    print(f"\nEjecutando: {' '.join(cmd)}\n")
    proc = subprocess.run(cmd, cwd=base)
    if proc.returncode == 0:
        if dry_run or choice == '1':
            print("\n✅ Vista previa completada.")
        else:
            out_file = output_args[1] if choice == '3' else 'estructura.txt'
            print(f"\n✅ Estructura guardada en: {out_file}")
    else:
        print("\n❌ Ocurrió un error. Por favor revisa los mensajes anteriores.")
        sys.exit(proc.returncode)

if __name__ == '__main__':
    main()
