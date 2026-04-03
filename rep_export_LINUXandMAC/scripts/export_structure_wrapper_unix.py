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

Utiliza `cli_utils_UNIX.py` para:
- prompt_yes_no, confirm_overwrite
- run_cmd con salida detallada
- get_additional_args
- safe_print para evitar errores Unicode
"""
import sys
from pathlib import Path

# Incluir carpeta padre para importar cli_utils
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rep_export_LINUXandMAC.cli_utils_UNIX import (
    prompt_yes_no,
    run_cmd,
    get_additional_args,
    confirm_overwrite,
    safe_print
)
from rep_export_LINUXandMAC.large_file_scanner import scan_large_files, fmt_size


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
    struct = base / 'generate_structure_UNIX.py'
    export = base / 'tiddler_exporter_UNIX.py'

    # Verificar scripts
    missing = [s for s in (struct, export) if not s.is_file()]
    if missing:
        safe_print(f"❌ No se encontraron: {', '.join(str(m) for m in missing)}")
        sys.exit(1)

    # Sobreescritura opcional de la raíz del repositorio
    root_override = None
    if prompt_yes_no("¿Especificar raíz del repositorio manualmente?", default=False):
        root_override = input("Ruta del repositorio objetivo: ").strip() or None

    # --- Escaneo de archivos grandes ---
    scan_root = Path(root_override) if root_override else base
    large_include = False
    large_action = 'preview'
    large_max_size = None

    try:
        stats = scan_large_files(scan_root)
    except Exception:
        stats = None

    if stats and stats.large:
        safe_print(f"\n⚠  Archivos grandes detectados: {len(stats.large)} archivo(s)")
        safe_print(f"   Repositorio: {stats.total} archivos  |  Media: {fmt_size(int(stats.mean))}  |  Mediana: {fmt_size(int(stats.median))}  |  P75: {fmt_size(int(stats.p75))}")
        safe_print(f"   Límite MAX sugerido: {fmt_size(stats.suggested_max_bytes)}")
        safe_print("   Top archivos grandes:")
        for fpath, fsize in stats.large[:5]:
            try:
                rel = fpath.relative_to(scan_root)
            except ValueError:
                rel = fpath
            safe_print(f"     {fmt_size(fsize):>10}  {rel}")
        safe_print("\n¿Qué hacer con los archivos grandes?")
        safe_print("  1) Omitir (default)")
        safe_print("  2) Incluir todos — modo: preview (primeros 64 KB de texto)")
        safe_print("  3) Incluir todos — modo: copy (copia gzip en tiddlers-export/large/)")
        safe_print("  4) Incluir todos — modo: embed (contenido completo en tiddler)")
        safe_print("  5) Ajustar límite MAX y re-evaluar")
        large_choice = input("Selecciona [1-5, Enter=1]: ").strip() or '1'
        if large_choice == '2':
            large_include, large_action = True, 'preview'
        elif large_choice == '3':
            large_include, large_action = True, 'copy'
        elif large_choice == '4':
            large_include, large_action = True, 'embed'
        elif large_choice == '5':
            try:
                mb = float(input(f"  Nuevo límite en MB [{stats.suggested_max_bytes // (1024*1024):.1f}]: ").strip() or str(stats.suggested_max_bytes / (1024*1024)))
                large_max_size = int(mb * 1024 * 1024)
                safe_print(f"  Límite establecido: {fmt_size(large_max_size)}")
                stats2 = scan_large_files(scan_root, large_max_size)
                safe_print(f"  Con este límite: {len(stats2.large)} archivo(s) grande(s)")
            except (ValueError, Exception):
                safe_print("  Valor inválido, se usará el límite por defecto.")
    elif stats:
        safe_print(f"\n✅ Sin archivos grandes detectados ({stats.total} archivos, máximo sugerido: {fmt_size(stats.suggested_max_bytes)})")

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
            out_name = input("Nombre de salida [estructura.txt]: ").strip() or 'estructura.txt'
            out_path = base / out_name
            if confirm_overwrite(out_path):
                args += ['--output', out_name, '--force']
                if root_override:
                    args += ['--root', root_override]
                safe_print("⏳ Generando estructura, esto puede tardar unos segundos...")
                code, _, _ = run_cmd([sys.executable, str(struct), '-v'] + args, cwd=base)
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
            # Pasar configuración de archivos grandes
            if large_include:
                exp_args += ['--include-large', '--large-action', large_action]
            if large_max_size is not None:
                exp_args += ['--max-size', str(large_max_size)]
            if root_override:
                exp_args += ['--root', root_override]
            code, _, _ = run_cmd([sys.executable, str(export)] + exp_args, cwd=base)
            if code != 0:
                if prompt_yes_no("Error al exportar. Volver al menú?", default=True):
                    continue
                sys.exit(code)
            if '--dry-run' in exp_args:
                safe_print("\n🚀 Ejecutando exportación real...")
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
