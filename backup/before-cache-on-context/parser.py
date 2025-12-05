from .utils import Context, Project, Version, Dependency, File
from . import logger

def get_compatible_version(
    version_list: list[Version],
    project: Project,
    ctx: Context,
    release_only: bool = False
    ) -> Version | None:
    """
    baseado no array de versões de um projeto, identifica qual deve ser o alvo de download
    o alvo vai ser definido como a primeira versão que:
        contenha uma versão compatível com a passada pra função
        e contenha um loader compatível com o passado pra função
    """
    
    modpack_game_version = ctx.version
    project_type = project.project_type
    slug = project.slug

    target = None
    for v in version_list:
        game_versions = v.game_versions
        if not modpack_game_version in game_versions:
            continue
        
        # só precisa verificar compatibilidade com o loader se for um mod
        if project_type == 'mod':
            loaders = v.loaders
            loader = ctx.loader
            if not loader in loaders:
                continue

        # só aceita versões estáveis
        if release_only:
            if not v.version_type == 'release':
                continue
        
        # se uma versão passar nas duas condições, ela é o alvo
        target = v
        break
    
    if target is None:
        logger.error('alvo não encontrado, possivelmente por não ser compatível com o loader ou versão', title=slug)
        return

    return target

def get_primary_jar(version: Version, ctx: Context):
    """
    obtém o arquivo primário que um mod precisa pra funcionar
    junto de um mod, podem vir arquivos extras, como código fonte, licenças etc.
    
    essa função garante que a única url de download obtida
    seja desse arquivo .jar primário
    """

    slug = version.project_id

    # obter a url e nome do arquivo .jar primário
    # é importante que esse nome não seja mudado pra que o cache de mods já baixados funcione normalmente
    files = version.files
    if len(files) > 1:
        logger.info('o projeto possui mais de um arquivo disponível. baixando apenas o primário', title=slug)

    primary = None
    for f in files:
        if not f.primary:
            continue
        
        primary = f
        break

    if primary is None:
        logger.warning('primário não encontrado, usando o primeiro item da lista como fallback', title=slug)
        primary = files[0]
    
    if primary is None:
        logger.error('o projeto não possui nenhum arquivo disponível', title=slug)
        return

    url = primary.url
    filename = primary.filename

    # retorna esses dois valores como tupla
    # devem ser desempacotados respectivamente ao usar a função
    return url, filename

def refine_version_list(data: list[dict], project_id: str) -> list[Version]:
    """
    reorganiza os dados de versões de um projeto vindos da api do modrinth

    transforma a lista de dicionários que a api retorna em uma lista de objetos
    Version, contendo as informações de cada versão, seus arquivos e dependências

    args:
        data:
            lista de dicionários representando cada versão de um projeto
        
        project_id:
            id do projeto pai, usado para associar cada versão a ele

    returns:
        lista de objetos Version com os arquivos e dependências estruturados
    """

    version_list = []

    for ver in data:
        files = []
        for f in ver.get('files'):
            files.append(
                File(
                    url=f.get('url'),
                    filename=f.get('filename'),
                    primary=f.get('primary')
                )
            )

        dependencies = []
        for d in ver.get('dependencies'):
            dependencies.append(
                Dependency(
                    project_id=d.get('project_id'),
                    dependency_type=d.get('dependency_type')
                )
            )

        version_list.append(
            Version(
                project_id=project_id,
                id=ver.get('id'),
                game_versions=ver.get('game_versions'),
                loaders=ver.get('loaders'),
                version_type=ver.get('version_type'),
                files=files,
                dependencies=dependencies
            )
        )

    return version_list