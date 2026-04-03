# Ejecución — Linux / macOS (usar cuando sólo pegaste `rep_export_LINUXandMAC`)

Guía rápida para ejecutar la herramienta después de copiar `rep_export_LINUXandMAC` dentro de otro repositorio.

## Escenario
Copiaste `rep_export_LINUXandMAC` al root del repo (por ejemplo `tools/repository-export` o en la raíz del proyecto).

## Requisitos
- Python 3.7+
- `tree` (opcional para estructura ASCII)
- bash/zsh

## Preparar el entorno
```bash
cd /ruta/al/repo
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install pathspec
# opcional (tests)
pip install pytest
```
Si `venv` falla por `ensurepip` revisa `README.md` para la opción `--without-pip` + `get-pip.py`.

## Uso interactivo (wrapper)
```bash
python3 rep-export-LINUXandMAC/scripts/export_structure_wrapper_unix.py
```
Elige `2` para exportar tiddlers JSON o `3` para generar estructura y exportar.

## Ejecución directa (dry-run)
```bash
python3 rep_export_LINUXandMAC/tiddler_exporter_UNIX.py --dry-run --root . --new-schema
```

## Ejecución real
```bash
python3 rep_export_LINUXandMAC/tiddler_exporter_UNIX.py --root . --new-schema
```
Incluyendo archivos grandes:
```bash
python3 rep_export_LINUXandMAC/tiddler_exporter_UNIX.py --root . --include-large --large-action preview
# forzar limite a 5MB
python3 rep_export_LINUXandMAC/tiddler_exporter_UNIX.py --root . --max-size 5242880
```
O usar variable de entorno:
```bash
export REPO_EXPORT_MAX_FILE_SIZE=5242880
python3 rep_export_LINUXandMAC/tiddler_exporter_UNIX.py --root . --include-large
```

## Verificar salida
```bash
ls -R tiddlers-export | sed -n '1,200p'
# ver un JSON
cat tiddlers-export/<archivo>.json | less
```

## Comprobaciones rápidas
```bash
python3 --version
python3 -c 'import sys; print(sys.executable)'
python3 -m pip --version
```

## Salir del venv
```bash
deactivate
# o cerrar la terminal
```

## Notas
- Usa `--dry-run` primero si no estás seguro del resultado.
- Si la carpeta está anidada y la detección de raíz no es la esperada, fuerza la raíz con `--root <ruta>` o define `REPO_EXPORT_ROOT`.
