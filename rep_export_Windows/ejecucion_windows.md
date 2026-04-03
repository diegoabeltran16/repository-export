# Ejecución — Windows (usar cuando sólo pegaste `rep_export_Windows`)

Este documento explica los pasos mínimos para usar `rep_export_Windows` después de copiar únicamente esa carpeta dentro de otro repositorio.

**Escenario:** copiaste la carpeta `rep_export_Windows` al root de tu repo (ej.: `tools/repository-export` o directamente en la raíz).

## Requisitos rápidos
- Python 3.7+
- PowerShell
- (Opcional) `tree` si quieres la opción de estructura ASCII

## Preparar el entorno
Abrir PowerShell en la raíz del repo (donde esté la carpeta `rep_export_Windows`) y crear/activar el venv:

```powershell
# crea y activa (usa el lanzador py para evitar problemas con ensurepip)
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1

# actualizar pip e instalar dependencia mínima
python -m pip install --upgrade pip
pip install pathspec
# opcional (tests)
pip install pytest
```

Si `venv` falla por `ensurepip`, ver `README.md` (opciones: `--without-pip`, `get-pip.py`, o `virtualenv`).

## Uso interactivo (wrapper)
Ejecuta el wrapper que muestra el menú y manejo de archivos grandes:

```powershell
python rep_export_Windows\scripts_windows\export_structure_wrapper_windows.py
```

- Elige `2` para exportar tiddlers (o `3` para generar estructura y exportar).
- Responde `y` si quieres `dry-run` primero (recomendado).

## Ejecución directa (dry-run)
Prueba sin escribir archivos:

```powershell
python rep_export_Windows\tiddler_exporter_windows.py --dry-run --root . --new-schema
```

## Ejecución real (genera JSON)
Para generar los tiddlers:

```powershell
python rep_export_Windows\tiddler_exporter_windows.py --root . --new-schema
```

Incluir archivos grandes (opciones: `preview`, `copy`, `embed`):

```powershell
python rep_export_Windows\tiddler_exporter_windows.py --root . --include-large --large-action copy
# o forzar límite a 5 MB
python rep_export_Windows\tiddler_exporter_windows.py --root . --max-size 5242880 --include-large --large-action preview
```

También puedes usar la variable de entorno:

```powershell
$env:REPO_EXPORT_MAX_FILE_SIZE = '5242880'
python rep_export_Windows\tiddler_exporter_windows.py --root . --include-large
```

## Verificar salida
Los tiddlers se escriben en `tiddlers-export/` (en la carpeta donde ejecutaste el script):

```powershell
Get-ChildItem -Recurse .\tiddlers-export\ | Select-Object FullName, Length
Get-Content .\tiddlers-export\<algún-archivo>.json -Raw
```

## Comprobaciones rápidas
```powershell
python --version
python -c "import sys; print(sys.executable)"
python -m pip --version
```

## Salir del `venv`
```powershell
deactivate
# o cerrar la ventana de la terminal
```

## Nota corta
- El wrapper hace un escaneo previo y ofrece opciones para archivos grandes; usa `dry-run` si no estás seguro.
- Si quieres integrarlo de forma limpia en muchos repos (recomendado), usa `git submodule` o los scripts de copia en `scripts/`.
