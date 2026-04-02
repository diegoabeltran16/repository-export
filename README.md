# 🧠 repository-export
[![CI - Run Tests](https://github.com/diegoabeltran16/repository-export/actions/workflows/python-tests.yml/badge.svg)](https://github.com/diegoabeltran16/repository-export/actions/workflows/python-tests.yml)

> Repositorio multiplataforma para exportar estructuras de proyectos y generar tiddlers TiddlyWiki con control de versiones y pruebas automatizadas.
**Automatiza la creación de documentación semántica a partir de cualquier repositorio de código.**
Convierte cada archivo fuente en un tiddler compatible con [TiddlyWiki](https://tiddlywiki.com), con etiquetas, fechas y contenido listo para navegar, estudiar o versionar.

---

## 🎯 Propósito del proyecto

Permite:
- Documentar código automáticamente
- Clasificar archivos por tipo o contexto semántico
- Versionar documentación sin esfuerzo
- Estudiar repositorios de terceros de forma estructurada

---

## 🛠️ ¿Qué hace?

✔️ Recorre todo el proyecto<br>
✔️ Detecta cambios reales en archivos<br>
✔️ Genera un archivo `.json` por cada archivo válido<br>
✔️ Cada archivo se convierte en un tiddler TiddlyWiki con:
- Título basado en su ruta
- Metadatos básicos (tipo detectado y fechas)
- Bloque de código con resaltado (`markdown`, `python`, `go`, etc.)
- Fecha de creación y modificación


---

## 💻 Uso básico

1. Clona el repositorio que deseas escanear y exportar
2. Dependiendo de tu sistema operativo (OS) descarga la carpeta 
rep-export-LINUXandMAC o rep-export-Windows
3. Pega la carpeta en tu repositorio y asegurate de tener:
**✅ Requisitos**
- Python 3.7+
- Comando `tree` instalado (`sudo apt install tree` o `brew install tree`)
- PowerShell (Windows) o bash/zsh (Unix)
4. (Opcional) Ajusta patrones de exclusión en `.gitignore` o usa `--exclude` / `--exclude-from` para filtrar qué se incluye.
5. Corre el comando que se ajuste a tus OS y elije el menu de opciones que se ajuste a tus necesidades

### Preparar entorno (recomendado)
Antes de ejecutar cualquier script, crea y activa un entorno virtual e instala la dependencia `pathspec`:

En Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install pathspec
```

En Linux / macOS (bash):
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install pathspec
```

Nota sobre detección de raíz: los scripts principales aceptan la opción `--root <ruta>` y respetan la variable de entorno `REPO_EXPORT_ROOT`. Úsalo cuando la herramienta esté anidada dentro de otro repositorio para forzar la raíz objetivo.

### Archivos grandes

Al iniciar el wrapper, se escanea el repositorio y se muestra un resumen estadístico (total de archivos, media, mediana, P75). Si hay archivos que superan el límite, el menú te pregunta qué hacer:

| Opción | Resultado |
|--------|-----------|
| 1 — Omitir (default) | Los archivos grandes se saltan |
| 2 — Preview | Se exporta un fragmento de hasta 64 KB |
| 3 — Copy | Se crea una copia gzip en `tiddlers-export/large/` |
| 4 — Embed | El contenido completo se incrusta en el tiddler |
| 5 — Ajustar límite | Permite redefinir el MAX y ver cuántos archivos quedan |

El límite por defecto es **1 MB**. Puedes sobrescribirlo de dos formas:

```bash
# Variable de entorno (persiste en la sesión)
export REPO_EXPORT_MAX_FILE_SIZE=5242880   # 5 MB

# Flag directo al exportador
python tiddler_exporter_windows.py --max-size 5242880
```

Luego ejecuta el wrapper correspondiente según tu OS:

**Nota:** La funcionalidad de carga de tags personalizados desde la carpeta `tiddler_tag_doc` ha sido desactivada. El exportador genera tiddlers JSON basados en la estructura y el contenido del repositorio, sin procesamiento semántico adicional.

### Linux / macOS
```bash
python3 rep-export-LINUXandMAC/scripts/export_structure_wrapper_unix.py
```

### Windows

```bash
python rep_export_Windows\scripts_windows\export_structure_wrapper_windows.py
```

### Uso interactivo (menú)
Los wrappers incluyen un menú interactivo que simplifica las tareas comunes. Al ejecutar el script verás opciones similares a:

- `1)` Generar estructura ASCII
- `2)` Exportar tiddlers JSON
- `3)` Generar estructura y exportar tiddlers
- `4)` Ayuda
- `5)` Salir

Selecciona la opción deseada escribiendo su número y sigue las indicaciones en pantalla (confirmaciones, flags adicionales, etc.).

## 🧭 ¿Para qué sirve?

| Caso | Beneficio |
|------|-----------|
| Estudiar un repo ajeno | Documentación lista para navegar |
| Auditar bugs o deuda técnica | Filtra por tags o analiza estructura |
| Automatizar CI/CD | Exportación controlada por cambios reales |
| Crear datasets para LLM | Markdown estructurado + semántica limpia |

---

## 🔎 Filosofía

- Modularidad
- Simplicidad (KISS)
- Documentación como parte del código
- Mantenibilidad multiplataforma

> “Cualquiera puede hablar, muestrame el codigo” — Linus Torvalds

---

## 📄 Licencia
Apache 2.0 — Puedes usarlo, modificarlo y distribuirlo libremente, siempre que mantengas el aviso de licencia y las condiciones incluidas. 
Este proyecto está hecho para crecer contigo.  
Úsalo, modifícalo, exprímelo.  
Y si lo mejoras: compártelo.
