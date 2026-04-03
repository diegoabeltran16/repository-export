#!/usr/bin/env bash
# scripts/copy_repo.sh
# Copia el contenido de repository-export a otro directorio excluyendo .git, .venv y tiddlers-export
# Uso: ./scripts/copy_repo.sh /ruta/al/repository-export /ruta/destino

set -euo pipefail
SRC=${1:-.}
DST=${2:-}

if [ -z "$DST" ]; then
  echo "Usage: $0 <source-dir> <dest-dir>"
  exit 2
fi

# Evitar copiar dentro de sí mismo
real_src=$(realpath "$SRC")
real_dst=$(realpath "$DST" 2>/dev/null || true)
if [ -n "$real_dst" ] && [[ "$real_dst" == "$real_src"* ]]; then
  echo "Error: destination must not be inside the source. Choose another folder."
  exit 3
fi

mkdir -p "$DST"

rsync -av --delete \
  --exclude='.git' \
  --exclude='.venv' \
  --exclude='tiddlers-export' \
  --exclude='__pycache__' \
  --exclude='.pytest_cache' \
  "${SRC%/}/" "$DST/"

echo "Copied ${SRC} -> ${DST} (excludes: .git, .venv, tiddlers-export)" 
