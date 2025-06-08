#!/usr/bin/env python3
"""
🤖 Asistente interactivo de exportación para Linux/macOS
Ubicación: rep-export-LINUXandMAC/scripts/export_structure_wrapper_unix.py

Guía paso a paso para:
 1) Generar estructura ASCII
 2) Exportar tiddlers JSON
 3) Ejecutar ambos secuencialmente
 4) Mostrar ayuda
 5) Salir

Utiliza `cli_utils.py` para:
- prompt_yes_no, confirm_overwrite
- run_cmd con salida detallada
- get_additional_args
- safe_print para evitar errores Unicode
"""
import sys
from pathlib import Path

# Incluir carpeta padre para importar cli_utils
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cli_utils import (
    prompt_yes_no,
    run_cmd,
    get_additional_args,
    confirm_overwrite,
    safe_print
)


def show_help():
    safe_print(__doc__)
    safe_print("Ejemplo: opción 3 ejecuta ambos pasos en secuencia.")


def get_menu_choice() -> str:
    choice = input("Selecciona [1-5]: ").strip()
    if choice not in ('1','2','3','4','5'):
        safe_print("❌ Opción inválida. Debe ser 1-5.")
        return get_menu_choice()
    return choice


def main():
    base = Path(__file__).resolve().parent.parent
    struct = base / 'generate_structure.py'
    export = base / 'tiddler_exporter.py'

    # Verificar scripts
    missing = [s for s in (struct, export) if not s.is_file()]
    if missing:
        safe_print(f"❌ No se encontraron: {', '.join(str(m) for m in missing)}")
        sys.exit(1)

    while True:
        safe_print("\n=== Menú de Opciones ===")
        safe_print("1) Generar estructura ASCII")
        safe_print("2) Exportar tiddlers JSON")
        safe_print("3) Generar estructura y exportar tiddlers")
        safe_print("4) Ayuda")
        safe_print("5) Salir")
        choice = get_menu_choice()

        if choice == '5':
            safe_print("👋 ¡Hasta luego!")
            break
        if choice == '4':
            show_help()
            continue

        # Paso 1: Generar estructura
        if choice in ('1','3'):
            safe_print("\n🛠️ Configuración Estructura ASCII")
            args = []
            if prompt_yes_no("¿Excluir patrones de .gitignore? (no oculta .gitignore)", default=False):
                args.append('--honor-gitignore')
            args += get_additional_args('generate_structure.py')
            out_name = input("Nombre de salida [estructura.txt]: ").strip() or 'estructura.txt'
            out_path = base / out_name
            if confirm_overwrite(out_path):
                args += ['--output', out_name]
                code, _, _ = run_cmd([sys.executable, str(struct)] + args, cwd=base)
                if code != 0:
                    if prompt_yes_no("Error al generar. Volver al menú?", default=True):
                        continue
                    sys.exit(code)
            else:
                safe_print("🔸 Generación de estructura cancelada.")

        # Paso 2: Exportar tiddlers
        if choice in ('2','3'):
            safe_print("\n🛠️ Configuración Exportación Tiddlers")
            exp_args = []
            if prompt_yes_no("¿Simulación (dry-run)?", default=False):
                exp_args.append('--dry-run')
            exp_args += get_additional_args('tiddler_exporter.py')
            code, _, _ = run_cmd([sys.executable, str(export)] + exp_args, cwd=base)
            if code != 0:
                if prompt_yes_no("Error al exportar. Volver al menú?", default=True):
                    continue
                sys.exit(code)
            if '--dry-run' in exp_args and prompt_yes_no("Dry-run completado. Ejecutar real?", default=True):
                real_args = [a for a in exp_args if a != '--dry-run']
                code, _, _ = run_cmd([sys.executable, str(export)] + real_args, cwd=base)
                if code != 0:
                    sys.exit(code)

        safe_print("\n✅ Operación completada con éxito.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        safe_print("\n⚠️ Interrupción por usuario. Saliendo...")
        sys.exit(1)
