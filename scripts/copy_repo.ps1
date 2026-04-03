# scripts/copy_repo.ps1
# Copia repository-export a otro directorio excluyendo .git, .venv y tiddlers-export
# Uso: .\scripts\copy_repo.ps1 -Source . -Dest D:\ruta\al\repo\tools\repository-export
param(
  [string]$Source = '.',
  [string]$Dest
)

if (-not $Dest) {
  Write-Host "Usage: .\scripts\copy_repo.ps1 -Source <source> -Dest <dest>"
  exit 2
}

$srcPath = (Resolve-Path -Path $Source).ProviderPath
$destPath = (Resolve-Path -LiteralPath $Dest -ErrorAction SilentlyContinue)
if (-not $destPath) { New-Item -ItemType Directory -Path $Dest | Out-Null }
$destPath = (Resolve-Path -Path $Dest).ProviderPath

# Prevención: no copiar dentro de sí mismo
if ($destPath.StartsWith($srcPath)) {
  Write-Error "Destination must not be inside the source. Choose another folder."; exit 3
}

# Robocopy. /MIR mirrors, /XD excludes directories
$excludeDirs = @('.git', '.venv', 'tiddlers-export', '__pycache__', '.pytest_cache')
$xd = $excludeDirs -join ' '

$robocopyArgs = @($Source, $Dest, '/MIR', '/R:2', '/W:2') + ('/XD') + $excludeDirs

# Ejecutar Robocopy
Write-Host "Running Robocopy from $Source to $Dest (excluding: $xd)"
robocopy @robocopyArgs | Out-Null

Write-Host "Copy complete: $Source -> $Dest"
