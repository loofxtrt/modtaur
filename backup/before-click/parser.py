from .constants import Context
from .cache import write_cache
from . import logger

def get_compatible_version(project_data: dict, project_type: str, slug: str, ctx: Context, release_only: bool = False) -> dict | None:
    """
    baseado no array de versões de um projeto, identifica qual deve ser o alvo de download
    o alvo vai ser definido como a primeira versão que:
        contenha uma versão compatível com a passada pra função
        e contenha um loader compatível com o passado pra função
    """
    
    version = ctx.version

    target = None
    for i in project_data:
        game_versions = i.get('game_versions')
        if not version in game_versions:
            continue
        
        # só precisa verificar compatibilidade com o loader se for um mod
        if project_type == 'mod':
            loaders = i.get('loaders')
            loader = ctx.loader
            if not loader in loaders:
                continue

        # só aceita versões estáveis
        if release_only:
            if not i.get('version_type') == 'release':
                continue
        
        # se uma versão passar nas duas condições, ela é o alvo
        target = i
        break
    
    if target is None:
        logger.error('alvo não encontrado, possivelmente por não ser compatível com o loader ou versão', title=slug)
        return

    return target

def get_primary_jar(compatible_version: dict, slug: str, ctx: Context):
    # obter a url e nome do arquivo .jar primário
    # é importante que esse nome não seja mudado pra que o cache de mods já baixados funcione normalmente
    files = compatible_version.get('files')
    if len(files) > 1:
        logger.info('o projeto possui mais de um arquivo disponível. baixando apenas o primário', title=slug)

    primary = None
    for f in files:
        if not f.get('primary', False):
            continue
        
        primary = f
        break

    if primary is None:
        logger.warning('primário não encontrado, usando o primeiro item da lista como fallback', title=slug)
        primary = files[0]
    
    if primary is None:
        logger.error('o projeto não possui nenhum arquivo disponível', title=slug)
        return

    url = primary.get('url')
    filename = primary.get('filename')

    # retorna esses dois valores como tupla
    # devem ser desempacotados respectivamente ao usar a função
    return url, filename