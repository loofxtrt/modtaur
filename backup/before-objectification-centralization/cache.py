from pathlib import Path

from .utils import write_json, read_json, Version, File, Dependency

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

    valid_data = None
    for f in cache_dir.rglob('*.json'):
        if not f.is_file():
            continue
        
        data = read_json(f)
        if data[0].get('project_id') == project_id:
            valid_data = data

    if valid_data:
        for v in valid_data:
            files = []
            for f in v.get('files'):
                files.append(
                    File(
                        url=f.get('url'),
                        filename=f.get('filename'),
                        primary=f.get('primary')
                    )
                )

            dependencies = []
            for d in v.get('dependencies'):
                dependencies.append(
                    Dependency(
                        project_id=d.get('project_id'),
                        dependency_type=d.get('dependency_type')
                    )
                )

            version_list.append(
                Version(
                    project_id=project_id,
                    id=v.get('id'),
                    game_versions=v.get('game_versions'),
                    loaders=v.get('loaders'),
                    version_type=v.get('version_type'),
                    files=files,
                )
            )
    
    return version_list