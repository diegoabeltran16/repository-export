import subprocess
import sys
from pathlib import Path
import pytest

def run_generate_structure(tmp_path, args=None):
    """
    Ejecuta generate_structure.py con --dry-run en el directorio tmp_path.
    Devuelve CompletedProcess.
    """
    script = Path(__file__).parent.parent / 'rep-export-LINUXandMAC' / 'generate_structure.py'
    cmd = [sys.executable, str(script), '--root', str(tmp_path), '--dry-run']
    if args:
        cmd.extend(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result


def test_default_excludes(tmp_path):
    # Crear estructura de prueba
    (tmp_path / 'keep_dir').mkdir()
    (tmp_path / 'keep_dir' / 'file.txt').write_text('hello')

    # Directorios y archivos que deben excluirse por defecto
    (tmp_path / '.git').mkdir()
    (tmp_path / '__pycache__').mkdir()
    (tmp_path / 'node_modules').mkdir()
    (tmp_path / 'secret.pyc').write_text('')
    (tmp_path / '.DS_Store').write_text('')

    # Ejecutar
    result = run_generate_structure(tmp_path)
    assert result.returncode == 0, f"Salida inesperada: {result.stderr}"
    output = result.stdout

    # Debemos ver keep_dir y file.txt
    assert 'keep_dir' in output
    assert 'file.txt' in output

    # No debe aparecer ninguna exclusión por defecto
    for excl in ['.git', '__pycache__', 'node_modules', 'secret.pyc', '.DS_Store']:
        assert excl not in output, f"Encontrado elemento excluido: {excl}"  


def test_custom_exclude_pattern(tmp_path):
    # Crear archivos de distintos tipos
    (tmp_path / 'logs').mkdir()
    (tmp_path / 'logs' / 'error.log').write_text('error')
    (tmp_path / 'data').mkdir()
    (tmp_path / 'data' / 'readme.md').write_text('# docs')

    # Ejecutar con patrón de exclusión para logs
    result = run_generate_structure(tmp_path, args=['-e', 'logs'])
    assert result.returncode == 0
    output = result.stdout

    # logs debe estar excluido, pero data debe aparecer
    assert 'logs' not in output
    assert 'data' in output

def test_honor_gitignore(tmp_path):
    # Crear .gitignore con patrón para temp*
    gitignore = tmp_path / '.gitignore'
    gitignore.write_text('temp*')

    # Crear archivos/directorios
    (tmp_path / 'temp123').mkdir()
    (tmp_path / 'keep').mkdir()

    # Ejecutar con honor-gitignore
    result = run_generate_structure(tmp_path, args=['--honor-gitignore'])
    assert result.returncode == 0
    output = result.stdout

    assert 'keep' in output
    assert 'temp123' not in output
