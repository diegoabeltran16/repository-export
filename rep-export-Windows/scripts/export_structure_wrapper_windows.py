#!/usr/bin/env python3
"""
🤖 Asistente interactivo de exportación para Windows
Ubicación: rep-export-Windows/scripts/export_structure_wrapper_windows.py

Guía paso a paso para:
 1) Generar estructura ASCII
 2) Exportar tiddlers JSON
 3) Ejecutar ambos secuencialmente
 4) Mostrar ayuda
 5) Salir

Características:
- Validación de entradas del usuario
- Ejecución de comandos con captura detallada (stdout, stderr, código)
- Abstracción de lógica común
- Soporte para argumentos adicionales
- Confirmación de sobrescritura de archivos
- Manejo de interrupción con Ctrl+C
"""
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def prompt_yes_no(question: str, default: bool = False) -> bool:
    default_str = 'S/n' if default else 's/N'
    while True:
        resp = input(f"{question} [{default_str}]: ").strip().lower()
        if not resp:
            return default
        if resp in ('s', 'si', 'y', 'yes'):
            return True
        if resp in ('n', 'no'):
            return False
        print("❗ Entrada inválida: responde 's' o 'n'.")


def run_cmd(cmd: List[str], cwd: Path) -> Tuple[int, str, str]:
    """Ejecuta comando y retorna (exit_code, stdout, stderr)."""
    print(f"\n▶️ Ejecutando: {' '.join(cmd)}\n")
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = proc.communicate()
    if out:
        print(out)
    if proc.returncode != 0:
        print(f"❌ Error (code {proc.returncode}) al ejecutar: {cmd[0]}")
        if err:
            print(f"📋 stderr:\n{err}")
    return proc.returncode, out, err


def get_additional_args(script: str) -> List[str]:
    """Solicita al usuario argumentos extra para un script."""
    extras = input(f"Argumentos extra para {script} (espacio-separated), o Enter para ninguno: ").strip()
    return extras.split() if extras else []


def confirm_overwrite(path: Path) -> bool:
    """Confirma sobrescritura si el archivo existe."""
    if path.exists():
        return prompt_yes_no(f"El archivo '{path.name}' ya existe. Sobrescribir?", default=False)
    return True


def show_help():
    print(__doc__)
    print("Ejemplo: en opción 3, se ejecutan ambos pasos en secuencia.")


def get_menu_choice() -> str:
    """Solicita y valida opción de menú."""
    valid = {'1','2','3','4','5'}
    choice = input("Selecciona [1-5]: ").strip()
    if choice not in valid:
        print("❌ Opción inválida. Debe ser 1,2,3,4 o 5.")
        return get_menu_choice()
    return choice


def main():
    try:
        base = Path(__file__).resolve().parent.parent
        struct_script = base / 'generate_structure.py'
        export_script = base / 'tiddler_exporter.py'

        # Verificar scripts
        missing = [s for s in (struct_script, export_script) if not s.is_file()]
        if missing:
            print(f"❌ No se encontraron: {', '.join(str(m) for m in missing)}")
            sys.exit(1)

        while True:
            print("\n=== Menú de Opciones ===")
            print("1) Generar estructura ASCII")
            print("2) Exportar tiddlers JSON")
            print("3) Generar estructura y exportar tiddlers")
            print("4) Ayuda")
            print("5) Salir")
            choice = get_menu_choice()

            if choice == '5':
                print("👋 ¡Hasta luego!")
                break
            if choice == '4':
                show_help()
                continue

            # Generar estructura
            if choice in ('1','3'):
                print("\n🛠️ Configuración Estructura ASCII")
                args = []
                if prompt_yes_no("¿Excluir patrones de .gitignore? (no oculta .gitignore)", default=False):
                    args.append('--honor-gitignore')
                args += get_additional_args('generate_structure.py')
                output_name = input("Nombre de salida [estructura.txt]: ").strip() or 'estructura.txt'
                out_path = base / output_name
                if not confirm_overwrite(out_path):
                    print("🔸 Generación de estructura cancelada.")
                else:
                    args += ['--output', output_name]
                    code, _, _ = run_cmd([sys.executable, str(struct_script)] + args, cwd=base)
                    if code != 0:
                        if prompt_yes_no("Error al generar. Volver al menú?", default=True):
                            continue
                        sys.exit(code)

            # Exportar tiddlers
            if choice in ('2','3'):
                print("\n🛠️ Configuración Exportación Tiddlers")
                exp_args = []
                if prompt_yes_no("¿Simulación (dry-run)?", default=False):
                    exp_args.append('--dry-run')
                exp_args += get_additional_args('tiddler_exporter.py')
                code, _, _ = run_cmd([sys.executable, str(export_script)] + exp_args, cwd=base)
                if code != 0:
                    if prompt_yes_no("Error al exportar. Volver al menú?", default=True):
                        continue
                    sys.exit(code)
                if '--dry-run' in exp_args and prompt_yes_no("Dry-run completado. Ejecutar real?", default=True):
                    real_args = [arg for arg in exp_args if arg != '--dry-run']
                    code, _, _ = run_cmd([sys.executable, str(export_script)] + real_args, cwd=base)
                    if code != 0:
                        sys.exit(code)

            print("\n✅ Operación completada con éxito.")
    except KeyboardInterrupt:
        print("\n⚠️ Interrupción por usuario. Saliendo...")
        sys.exit(1)

if __name__ == '__main__':
    main()
