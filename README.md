# 🧠 repository-export

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
- Tags (por tipo de archivo o definidos por plantilla)
- Bloque de código con resaltado (`markdown`, `python`, `go`, etc.)
- Fecha de creación y modificación

---

## 💻 Uso básico

### Linux / macOS
```bash
python3 rep-export-LINUXandMAC/generate_structure.py
python3 rep-export-LINUXandMAC/tiddler_exporter.py
```

### Windows
```powershell
python rep-export-Windows/generate_structure.py
python rep-export-Windows/tiddler_exporter.py
```

### Opción: modo simulación (sin escribir archivos)
```bash
python3 .../tiddler_exporter.py --dry-run
```

---

## 🧩 Tags automáticos y personalizados

📁 Si deseas control total sobre las etiquetas, crea archivos `.json` dentro de:
- `rep-export-LINUXandMAC/tiddler_tag_doc/`
- `rep-export-Windows/tiddler_tag_doc/`

Ejemplo:
```json
[
  { "title": "-src_utils_math.py", "tags": "[[Python]] [[Math]]" },
  { "title": "-README.md", "tags": "[[Markdown]] [[📘 Doc]]" }
]
```

🧠 Si no se encuentra ningún tag definido, se asigna uno según el tipo de archivo (p. ej. `.js` → `[[JavaScript]]`)

📌 Si el archivo no tiene extensión reconocida, se etiqueta como: `[[--- 🧬 Por Clasificar]]`

---

## 🧪 Control por hash

🔐 Para evitar redundancia, el sistema genera tiddlers **solo si el archivo cambió**.  
Se calcula un hash SHA-1 del contenido y se guarda en `.hashes.json`.

---

## 📂 Carpeta de salida

Los tiddlers generados van a:
- `rep-export-Windows/tiddlers-export/`
- `rep-export-LINUXandMAC/tiddlers-export/`

Puedes importar estos `.json` directamente a TiddlyWiki (HTML offline o web).

---

## 🧭 ¿Para qué sirve?

| Caso | Beneficio |
|------|-----------|
| Estudiar un repo ajeno | Documentación viva lista para navegar |
| Auditar bugs o deuda técnica | Filtra por tags o analiza estructura |
| Enseñar con ejemplos reales | Cada archivo es una unidad didáctica |
| Automatizar CI/CD | Exportación controlada por cambios reales |
| Crear datasets para LLM | Markdown estructurado + semántica limpia |

---

## 🔎 Filosofía

- 🧱 Modularidad
- 🧠 Simplicidad (KISS)
- 📚 Documentación como parte del código
- 💡 Mantenibilidad multiplataforma

> “El código solo es bueno si se puede entender” — Linus Torvalds

---

## ✅ Requisitos
- Python 3.7+
- Comando `tree` instalado (`sudo apt install tree` o `brew install tree`)
- PowerShell (Windows) o bash/zsh (Unix)

---

## 🚀 Contribuir
Este proyecto está hecho para crecer contigo.  
Úsalo, modifícalo, exprímelo.  
Y si lo mejoras: compártelo.

---

## 📄 Licencia
Apache 2.0 — Puedes usarlo, modificarlo y distribuirlo libremente, siempre que mantengas el aviso de licencia y las condiciones incluidas.
