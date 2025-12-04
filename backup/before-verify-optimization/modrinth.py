from pathlib import Path
import requests
import shutil

from .utils import Context, API_BASE, HEADERS, Project, Version, Dependency
from .parser import get_compatible_version, get_primary_jar
from .cache import get_cached_project_data, write_cache
from . import logger

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

def _request_project_data(slug: str, section: str | None = 'version'):
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

    # construir a url que dá acesso a api do modrinth
    project = f'{API_BASE}/project/{slug}'
    if section == 'version':
        project += '/version'
    try:
        response = requests.get(project, headers=HEADERS)
        response.raise_for_status() # evidencia erros caso eles ocorram

        response = response.json() # transforma a resposta de texto em json
        return response
    except requests.exceptions.HTTPError:
        logger.error(f'não foi possível obter os dados do projeto. isso provavelmente aconteceu por um slug inexistente', title=slug)
        return

def get_version_list(slug: str) -> list[Version]:
    data = _request_project_data(slug)
    version_list = []

    for v in data:
        raw_deps = v.get('dependencies', [])
        dependencies = _load_depencencies(raw_deps)

        version = Version(
            _parent_slug=slug,
            game_versions=v.get('game_versions'),
            loaders=v.get('loaders'),
            id=v.get('id'),
            version_type=v.get('version_type'),
            files=v.get('files'),
            dependencies=dependencies
        )
        version_list.append(version)
    
    return version_list

def get_project(slug: str) -> Project:
    data = _request_project_data(slug, section=None)
    return Project(
        game_versions=data.get('game_versions'),
        project_type=data.get('project_type'),
        id=data.get('id'),
        slug=slug,
        loaders=data.get('loaders')
    )

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

    dependencies = []

    for raw in raw_deps:
        # esse project_id não se refere a quem requisitou essa dependência
        # ele se refere ao projeto da dependência em si
        project_id = raw.get('project_id')

        d = Dependency(
            _slug=get_slug_from_id(project_id),
            project_id=project_id,
            dependency_type=raw.get('dependency_type')
        )
        dependencies.append(d)

    return dependencies

def resolve_dependencies(dependencies: list[Dependency], parent_slug: str, ctx: Context):
    """
    verifica quais dependências são obrigatórias pro funcionamento de um projeto e as baixa
    """

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
        
        dependency_slug = d._slug
        project = get_project(dependency_slug)
        project_type = project.project_type

        resolve_project_downloading(dependency_slug, project_type, ctx, is_dependency_for=parent_slug)

def get_slug_from_id(project_id: str):
    """
    obtém o slug (indentificador legível)
    a partir do id (identificador aleatório) de um projeto
    """

    data = _request_project_data(project_id, section=None)
    return data.get('slug')

def resolve_project_downloading(slug: str, project_type: str, ctx: Context, is_dependency_for: str | None = None):
    """
    args:
        slug:
            identificador legível do projeto
        
        project_type:
            mod, resourcepack etc.
        
        is_dependency_for:
            se é uma dependência de algum outro projeto, deve ser espeficado
            isso serve pro log ser mais detalhado        
    """

    def _install_predownloaded(target: Path, dependencies: list[Dependency]):
        resolve_dependencies(dependencies, slug, ctx)
        shutil.copy2(target, dir_destination)

        logger.success('mod já baixado encontrado', title=slug, nerdfont_icon=nerdfont_icon, details=dependency_label)

    def _search_predownloaded():
        return dir_predownloaded.rglob(f'*{suffix_type}')

    version = ctx.version
    loader = ctx.loader
    dir_predownloaded = ctx.dir_predownloaded

    dir_destination = None
    suffix_type = None

    if project_type == 'mod':
        dir_destination = ctx.dir_mods
        suffix_type = '.jar'
    elif project_type == 'resourcepack':
        dir_destination = ctx.dir_resourcepacks
        suffix_type = '.zip'
    
    if not dir_destination or not suffix_type:
        logger.error(f'{project_type} não parece ser um tipo válido de projeto do modrinth')
        return

    # construção de caminhos de pré-baixados e cache
    # + s no final mod -> mods, resourcepack -> resourcepacks
    subdown = dir_predownloaded / version / (project_type + 's')
    if is_dependency_for is not None:
        subdown = subdown / 'dependencies'

    subdown.mkdir(exist_ok=True, parents=True)
    cache_file = subdown / '.cache.json'

    # definir argumentos pro log
    nerdfont_icon = logger.DEFAULT_NERDFONT_ICON
    dependency_label = None
    if is_dependency_for is not None:
        dependency_label = f'é uma dependência de {is_dependency_for}'
        nerdfont_icon = '󰆦'

    # tentar obter o projeto pelo cache e pelo diretório de pré-baixados
    # antes de tentar fazer uma requisição pra api e baixar pela web
    cached = get_cached_project_data(slug, cache_file)
    if cached:
        filename = cached.get('filename')

        for f in _search_predownloaded():
            if f.name == filename:
                raw_deps = cached.get('dependencies', [])
                dependencies = _load_depencencies(raw_deps)

                _install_predownloaded(f, dependencies)
                return

    project = get_project(slug)
    version_list = get_version_list(slug)
    compatible_version = get_compatible_version(version_list, project, project_type, ctx)
    if not compatible_version:
        return

    dependencies = compatible_version.dependencies
    url, filename = get_primary_jar(compatible_version, ctx)

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