from pathlib import Path
from dataclasses import asdict
import json

from .utils import write_json, read_json, Version, File, Dependency
from .parser import refine_version_list

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

def get_cached_version_list(project_id: str, cache_dir: Path) -> list[Version]:
    version_list = []

    # procurar um arquivo a partir do diretório de cache
    # que corresponda ao id passado pra essa função
    # se achar, reformata e retorna essa lista
    valid_data = None
    for f in cache_dir.rglob('*.json'):
        if not f.is_file():
            continue
        
        data = read_json(f)
        if not isinstance(data, list):
            continue
    
        if data[0].get('project_id') == project_id:
            valid_data = data

    if valid_data:
        for v in valid_data:
            version_list = refine_version_list(data=valid_data, project_id=project_id)
    
    return version_list

def write_version_list_cache(version_list: list[Version], file: Path):
    """
    converte uma lista de Version pra um dicionário comum
    e escreve esses dados num json
    """

    dictfied = [ asdict(v) for v in version_list ]
    write_json(file, dictfied)