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

Utiliza `cli_utils.py` para:
- prompt_yes_no, confirm_overwrite
- run_cmd con salida detallada
- get_additional_args
- safe_print para evitar errores Unicode
"""
import sys
from pathlib import Path

# Incluir carpeta padre en path para importar cli_utils
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import cli_utils_Windows


def show_help():
    cli_utils_Windows.safe_print(__doc__)
    cli_utils_Windows.safe_print("Ejemplo: opción 3 ejecuta los dos pasos en secuencia.")


def get_menu_choice() -> str:
    choice = input("Selecciona [1-5]: ").strip()
    if choice not in ('1','2','3','4','5'):
        cli_utils_Windows.safe_print("❌ Opción inválida. Debe ser 1-5.")
        return get_menu_choice()
    return choice


def main():
    base = Path(__file__).resolve().parent.parent
    struct = base / 'generate_structure_windows.py'
    export = base / 'tiddler_exporter_windows.py'

    # Verificar scripts
    missing = [s for s in (struct, export) if not s.is_file()]
    if missing:
        cli_utils_Windows.safe_print(f"❌ No se encontraron: {', '.join(str(m) for m in missing)}")
        sys.exit(1)

    while True:
        cli_utils_Windows.safe_print("\n=== Menú de Opciones ===")
        cli_utils_Windows.safe_print("1) Generar estructura ASCII")
        cli_utils_Windows.safe_print("2) Exportar tiddlers JSON")
        cli_utils_Windows.safe_print("3) Generar estructura y exportar tiddlers")
        cli_utils_Windows.safe_print("4) Ayuda")
        cli_utils_Windows.safe_print("5) Salir")
        choice = get_menu_choice()

        if choice == '5':
            cli_utils_Windows.safe_print("👋 ¡Hasta luego!")
            break
        if choice == '4':
            show_help()
            continue

        # Paso 1: Generar estructura
        if choice in ('1','3'):
            cli_utils_Windows.safe_print("\n🛠️ Configuración Estructura ASCII")
            args = []
            if cli_utils_Windows.prompt_yes_no("¿Excluir patrones de .gitignore? (no oculta .gitignore)", default=False):
                args.append('--honor-gitignore')
            args += cli_utils_Windows.get_additional_args('generate_structure.py')
            out_name = input("Nombre de salida [estructura.txt]: ").strip() or 'estructura.txt'
            out_path = base / out_name
            if cli_utils_Windows.confirm_overwrite(out_path):
                args += ['--output', out_name, '--force']
                cli_utils_Windows.safe_print("⏳ Generando estructura, esto puede tardar unos segundos...")  # <-- NUEVO
                code, _, _ = cli_utils_Windows.run_cmd([sys.executable, str(struct), '-v'] + args, cwd=base)
                if code != 0:
                    if cli_utils_Windows.prompt_yes_no("Error al generar. Volver al menú?", default=True):
                        continue
                    sys.exit(code)
            else:
                cli_utils_Windows.safe_print("🔸 Generación de estructura cancelada.")

        # Paso 2: Exportar tiddlers
        if choice in ('2','3'):
            cli_utils_Windows.safe_print("\n🛠️ Configuración Exportación Tiddlers")
            exp_args = []
            if cli_utils_Windows.prompt_yes_no("¿Simulación (dry-run)?", default=False):
                exp_args.append('--dry-run')
            # Pregunta si quiere usar el nuevo esquema
            if cli_utils_Windows.prompt_yes_no("¿Usar nuevo esquema de exportación (tags_list y relations)?", default=True):
                exp_args.append('--new-schema')
            exp_args += cli_utils_Windows.get_additional_args('tiddler_exporter.py')
            code, _, _ = cli_utils_Windows.run_cmd([sys.executable, str(export)] + exp_args, cwd=base)
            if code != 0:
                if cli_utils_Windows.prompt_yes_no("Error al exportar. Volver al menú?", default=True):
                    continue
                sys.exit(code)
            if '--dry-run' in exp_args and cli_utils_Windows.prompt_yes_no("Dry-run completado. Ejecutar real?", default=True):
                real_args = [a for a in exp_args if a != '--dry-run']
                code, _, _ = cli_utils_Windows.run_cmd([sys.executable, str(export)] + real_args, cwd=base)
                if code != 0:
                    sys.exit(code)

        cli_utils_Windows.safe_print("\n✅ Operación completada con éxito.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        cli_utils_Windows.safe_print("\n⚠️ Interrupción por usuario. Saliendo...")
        sys.exit(1)
