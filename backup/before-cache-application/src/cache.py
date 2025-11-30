from .utils import write_json, read_json
from .constants import Context

def write_cache(slug: str, filename: str, ctx: Context):
    """
    escreve em um cache, quais slugs estão associados a quais filenames
    
    isso evita ter que fazer uma nova chamada pra api do modrinth
    só pra verificar se um filename já está presente no diretório de pré-baixados
    """

    dir_predownloaded = ctx.dir_predownloaded
    version = ctx.version

    data = {}

    # ler possíveis dados já existentes
    cache = dir_predownloaded / version / '.cache.json'
    data = read_json(cache)

    # adicionar o novo par aos dados e atualizar o arquivo
    data[slug] = filename
    
    write_json(cache, data)

def get_cached_filename(slug: str, ctx: Context) -> str | None:
    dir_predownloaded = ctx.dir_predownloaded
    version = ctx.version

    cache = dir_predownloaded / version / '.cache.json'
    data = read_json(cache)

    filename = data.get(slug)
    return filename