from pathlib import Path
import requests
import shutil

from .utils import Context, API_BASE, HEADERS, Project, Version, Dependency, File, ensure_directory
from .parser import get_compatible_version, get_primary_jar, refine_version_list
from .cache import get_cached_version_list, write_cache, write_version_list_cache
from . import logger

def _load_depencencies(raw_deps: list[dict]) -> list[Dependency]:
    """
    converte uma lista de dict em uma lista de Dependency
    isso serve pra que informações vindas do modrinth possam ser entendidas pelo software

    args:
        raw_deps:
            a lista de dicionários que aparece em cada versão individual do projeto. ex:
            lista-de-versoes: [
                versao: {
                    mais-informacoes: lorem ipsum
                    dependencias: [ <- essa lista
                        {
                            informacoes-da-dependencia
                        }
                    ]
                }
            ]
    """

    logger.debug('...', title='load dependencies')

    dependencies = []

    for raw in raw_deps:
        # esse project_id não se refere a quem requisitou essa dependência
        # ele se refere ao projeto da dependência em si
        project_id = raw.get('project_id')

        d = Dependency(
            project_id=project_id,
            dependency_type=raw.get('dependency_type')
        )
        dependencies.append(d)

    return dependencies

def _request_project_data(slug: str, section: str | None):
    """
    obtém os dados de um projeto do modrinth
    projetos se referem a mods, resourcepacks e datapacks

    eles são requisitados pela url da api + /version
    isso retorna um array com dicionários que representam cada versão do mod

    as principais chaves dentro de cada um desses dicionários são:
        game_versions:
            versões em que o mod é compatível
        
        loaders:
            quais loaders podem ser usados pra rodar o mod
        
        files:
            contém os arquivos do mod

            na maioria das vezes um mod é contido em um único .jar,
            mas alguns projetos podem ter múltiplos arquivos nessa lista,
            como por exemplo, código fonte, licenças etc.

            o que diferencia o .jar relevante dos adicionais é a chave 'primary'
            se ela for true, significa que aquele é o .jar que realmente é o mod
            se ela não for true em nenhum dos itens, como fallback, pode se assumir
            que o primerio item da lista de ser considerado como primário
        
        dependencies:
            contém dependencias necessárias pro funcionamento do mod pai

            elas são listadas contendo o id dos projetos delas em vez do slug,
            mas isso funciona do mesmo modo que um slug funcionaria
    
    args:
        slug:
            identificador do mod. pode ser tanto um slug literal, como 'sodium'
            ou um id gerado aleatoriamente, como 'AANobbMI'
        
        section:
            define qual de dados seção vai ser obtida
            'version' dá acesso a todas as versões que o mod já teve
            a ausência desse valor resulta em dados gerais sobre o projeto
    """

    logger.debug(slug, title='request project data')

    # construir a url que dá acesso a api do modrinth
    project = f'{API_BASE}/project/{slug}'
    if section == 'version':
        project += '/version'

    try:
        response = requests.get(project, headers=HEADERS)
        response.raise_for_status() # evidencia erros caso eles ocorram

        response = response.json() # transforma a resposta de texto em json
        logger.debug('informações do projeto obtidas', title=slug)

        return response
    except requests.exceptions.HTTPError:
        logger.error(f'não foi possível obter os dados do projeto. isso provavelmente aconteceu por um slug inexistente', title=slug)
        return

def download_file(url: str, filename: str, destination_dir: Path):
    """
    baixa o .jar atribuído a um mod. os valores que identificam esse jar
    devem ter sido anteriormente já extraído dos dados do projeto
    
    args:
        url:
            url do jar. geralemente fica em:
            0 > files > 0 > url
            com 0 podendo variar dependendo do índice
        
        filename:
            o nome do arquivo final,
            também é encontrado no mesmo nível da url
        
        destination_dir:
            lugar de destino do arquivo baixado
            geralmente é a .minecraft/mods
    """

    logger.debug(url, title='download file')

    if not destination_dir.is_dir():
        logger.error(f'{destination_dir} não é um diretório')
        return
    destination = destination_dir / filename
    
    down = requests.get(url, stream=True) # stream baixa em chunks
    down.raise_for_status()

    # write bytes, baixa em chunks de 8192 mb
    # o programa não inicia o próximo até a conclusão desse
    with destination.open('wb') as dest:
        for chunk in down.iter_content(chunk_size=8192):
            dest.write(chunk)

    return destination

def get_version_list(slug: str) -> list[Version]:
    """
    reestrutura os dados da api do modrinth pra serem uma lista de Version
    mais informações sobre isso na função refine_version_list
    """

    logger.debug(slug, title='get version list')

    data = _request_project_data(slug, section='version')
    version_list = refine_version_list(data, slug)
    
    return version_list

def get_project(slug: str, treat_plugin_as_mod: bool = True) -> Project:
    """
    args:
        treat_plugin_as_mod:
            pra casos tipo o do worldedit, que têm uma versão em plugin
            mas também funcionam como mod normalmente

            se o projeto em questão tiver o tipo como 'plugin'
            ele vai convertido e tratado como 'mod'
    """

    logger.debug(slug, title='get project')

    data = _request_project_data(slug, section=None)
    project_type = data.get('project_type')

    if treat_plugin_as_mod and project_type == 'plugin':
        project_type = 'mod'

    return Project(
        game_versions=data.get('game_versions'),
        project_type=project_type,
        id=data.get('id'),
        slug=slug,
        loaders=data.get('loaders')
    )

def resolve_dependencies(dependencies: list[Dependency], parent_slug: str, ctx: Context):
    """
    verifica quais dependências são obrigatórias pro funcionamento de um projeto e as baixa
    """

    logger.debug(parent_slug, title='resolve dependencies')

    dir_mods = ctx.dir_mods

    if not dir_mods.is_dir():
        logger.error(f'{dir_mods} não é um diretório')
        return

    if len(dependencies) == 0:
        return

    # baixar cada dependência
    for d in dependencies:
        if not d.dependency_type == 'required':
            continue
        
        # não continuar caso essa dependência já tenha sido resolvida
        # caso contrário, adiciona ela no set de resolvidas e prossegue
        project_id = d.project_id
        if project_id in ctx.resolved:
            continue

        ctx.resolved.add(project_id)
        project = get_project(project_id)

        resolve_project_downloading(project=project, ctx=ctx, is_dependency_for=parent_slug)

def resolve_project_downloading(
    project: Project,
    ctx: Context,
    is_dependency_for: str | None = None
    ):
    """
    args:
        is_dependency_for:
            se é uma dependência de algum outro projeto, deve ser espeficado
            isso serve pro log ser mais detalhado        
    """

    def _install_predownloaded(target: Path, dependencies: list[Dependency]):
        resolve_dependencies(dependencies, slug, ctx)
        shutil.copy2(target, dir_destination)

        logger.success(
            'mod já baixado encontrado',
            title=slug, details=dependency_label,
            nerdfont_icon=nerdfont_icon
        )

    def _search_predownloaded():
        return cache_root.rglob(f'*{suffix_type}')

    slug = project.slug
    project_type = project.project_type
    id = project.id

    version = ctx.version
    loader = ctx.loader
    cache_root = ctx.cache_root
    dotminecraft = ctx.dotminecraft

    logger.debug(slug, title='resolve project downloading')
    
    dir_destination = None
    suffix_type = None

    if project_type == 'mod':
        dir_destination = dotminecraft.mods
        suffix_type = '.jar'
    elif project_type == 'resourcepack':
        dir_destination = dotminecraft.resourcepacks
        suffix_type = '.zip'
    else:
        logger.error(f'{project_type} não parece ser um tipo válido de projeto do modrinth')
        return

    # construção de caminhos de pré-baixados e cache
    # + s no final mod -> mods, resourcepack -> resourcepacks
    cached_dest = cache_root / (project_type + 's') / version
    if is_dependency_for is not None:
        cached_dest = cached_dest / 'dependencies'
    ensure_directory(cached_dest)

    cache_version_dir = ctx.dir_cache_version_lists
    123[] #FIXME cache_version_dir.mkdir(exist_ok=True, parents=True)

    # definir argumentos pro log
    nerdfont_icon = logger.DEFAULT_NERDFONT_ICON
    dependency_label = None
    if is_dependency_for is not None:
        dependency_label = f'é uma dependência de {is_dependency_for}'
        nerdfont_icon = '󰏖'

    # tentar obter o projeto pelo cache e pelo diretório de pré-baixados
    # antes de tentar fazer uma requisição pra api e baixar pela web
    version_list = get_cached_version_list(id, cache_version_dir)
    if version_list:
        compatible = get_compatible_version(version_list, project, ctx)
        if compatible:
            url, filename = get_primary_jar(compatible, ctx)

            for f in _search_predownloaded():
                if f.name == filename:
                    dependencies = compatible.dependencies
                    _install_predownloaded(f, dependencies)
                    return

    version_list = get_version_list(slug)
    write_version_list_cache(version_list, cache_version_dir / f'{slug}.json')
    compatible = get_compatible_version(version_list, project, ctx)
    if not compatible:
        return

    dependencies = compatible.dependencies
    url, filename = get_primary_jar(compatible, ctx)

    # depois de obter os dados, resolve as dependências, baixando as necessárias
    resolve_dependencies(dependencies, slug, ctx)

    # tentar só encontrar mods pré-baixados de novo
    # se isso não for feito novamente, mesmo que o mod já esteja pré-baixado
    # o download dele seria feito de novo (se esse mod já não estiver no cache)
    for f in _search_predownloaded():
        if f.name == filename:
            _install_predownloaded(f, dependencies)
            return

    # baixar o arquivo triggando um spinner pro carregamento do download
    with logger.spinner(title=slug, details=dependency_label):
        dest = download_file(url, filename, dir_destination)
    
    # copiar pro diretório de já baixados pra não precisar baixar de novo
    shutil.copy2(dest, subdown)