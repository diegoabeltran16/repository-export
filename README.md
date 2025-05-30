# repository-export
Repository Export automatiza la documentación semántica de proyectos, generando tiddlers compatibles con TiddlyWiki a partir del código fuente

## Propósito del proyecto
Este proyecto nace como una solución a la falta de herramientas que combinen:
- Estructura del código
- Clasificación semántica
- Exportación portable
Su objetivo es ayudar a mantener documentación viva, curada y sincronizada con el código, ideal para programadores, investigadores y equipos técnicos.

## 🔧 Tecnologías y conceptos aplicados:

- Python scripting avanzado
- Estructuración de proyectos
- Automatización y CLI
- Control por hashes (detección de cambios)
- Documentación semántica (tags)
- Compatibilidad con TiddlyWiki
- Buenas prácticas: modularidad, legibilidad, extensibilidad

## Flujo de trabajo
1. Genera la estructura del repositorio (`estructura.txt`)
2. Asigna tags personalizados desde un JSON centralizado (Si aplica)
3. Detecta cambios en archivos fuente
4. Exporta solo los archivos modificados como tiddlers (`.json`)
5. Listos para ser importados en TiddlyWiki

## Cómo usarlo


## Motivación personal
Este proyecto refleja mi interés en crear herramientas que combinan código, estructura y conocimiento.
Busco que el código no solo funcione, sino que **cuente una historia clara, viva y reutilizable**.
Repository Export es parte de mi búsqueda por hacer el conocimiento técnico más accesible, legible y portable.

## Resultado final
🎯 Archivos fuente convertidos en tiddlers `.json`
📦 Documentación técnica clasificada semánticamente
🧠 Control de cambios y automatización lista para CI/CD

