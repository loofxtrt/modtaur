from pathlib import Path

from .utils import write_json, read_json

def write_cache(slug: str, filename: str, dependencies: list, cache_file: Path):
    """
    escreve em um cache, quais slugs estão associados a quais filenames
    
    isso evita ter que fazer uma nova chamada pra api do modrinth
    só pra verificar se um filename já está presente no diretório de pré-baixados
    """

    data = {}

    # ler possíveis dados já existentes
    data = read_json(cache_file)

    # adicionar o novo par aos dados e atualizar o arquivo
    data[slug] = {
        'filename': filename,
        'dependencies': dependencies
    }
    
    write_json(cache_file, data)

def get_cached_project_data(slug: str, cache_file: Path) -> dict | None:
    data = read_json(cache_file)
    cached_project = data.get(slug)

    return cached_project