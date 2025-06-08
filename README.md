# 🧠 repository-export

[![Linux/macOS CI](https://github.com/diegoabeltran16/repository-export/actions/workflows/linux-mac.yml/badge.svg)](https://github.com/diegoabeltran16/repository-export/actions/workflows/linux-mac.yml)
[![Windows CI](https://github.com/diegoabeltran16/repository-export/actions/workflows/windows.yml/badge.svg)](https://github.com/diegoabeltran16/repository-export/actions/workflows/windows.yml)

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
- Tags (por tipo de archivo o definidos por plantilla)
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
4. (Opcional) Si tienes una estructura de tags en tu Tiddler puedes pegar la exportacion en formato .JSON en la carpeta: \tiddler_tag_doc
5. Corre el comando que se ajuste a tus OS y elije el menu de opciones que se ajuste a tus necesidades

### Linux / macOS
```bash
python3 rep-export-LINUXandMAC/scripts/export_structure_wrapper_unix.py
```

### Windows

```bash
python rep-export-Windows/scripts/export_structure_wrapper_windows.py
```
6. Revisa la carpeta \tiddlers-export que debio crearse automaticamente , alli encontraras los tiddlers convertidos en formato .JSON

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

> “Cualquiera puede hablar, muestrame el codigo” — Linus Torvalds

---

## 🚀 Contribuir
Este proyecto está hecho para crecer contigo.  
Úsalo, modifícalo, exprímelo.  
Y si lo mejoras: compártelo.

---

## 📄 Licencia
Apache 2.0 — Puedes usarlo, modificarlo y distribuirlo libremente, siempre que mantengas el aviso de licencia y las condiciones incluidas.
