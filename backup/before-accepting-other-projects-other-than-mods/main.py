from pathlib import Path
from dataclasses import dataclass
import shutil
import json
import requests

import logger

DOTMINECRAFT = Path.home() / '.minecraft'
API_BASE = 'https://api.modrinth.com/v2'
HEADERS = {"User-Agent": "modtaur/0.1"}

@dataclass
class Context():
    """
    args:
        slug:
            identificador úncio do mod. ex: modrinth.com/mod/sodium

            pode ser tanto uma string entendível ou uma sequência de chars aleatória
            ambos funcionam pra chegar na mesma url
        
        version:
            versão do minecraft
        
        loader:
            fabric, forge etc.
        
        dir_predownloaded:
            mods já baixados que podem ser reutilizados
            em vez de precisar baixar eles de novo pra um  novo modpack
        
        dir_mods:
            ~/.minecraft/mods
    """

    version: str
    loader: str
    dir_predownloaded: Path
    dir_mods: Path

def download_jar(url: str, filename: str, destination_dir: Path):
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

def get_project_data(slug: str, section: str | None = 'version'):
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

def get_compatible_version(project_data: dict, slug: str, ctx: Context, release_only: bool = False) -> dict | None:
    """
    baseado no array de versões de um projeto, identifica qual deve ser o alvo de download
    o alvo vai ser definido como a primeira versão que:
        contenha uma versão compatível com a passada pra função
        e contenha um loader compatível com o passado pra função
    """
    
    version = ctx.version
    loader = ctx.loader

    target = None
    for i in project_data:
        game_versions = i.get('game_versions')
        if not version in game_versions:
            continue

        loaders = i.get('loaders')
        if not loader in loaders:
            continue

        if release_only:
            if not i.get('version_type') == 'release':
                # só aceita versões estáveis
                continue
        
        # se uma versão passar nas duas condições, ela é o alvo
        target = i
        break
    
    if target is None:
        logger.error('alvo não encontrado, possivelmente por não ser compatível com o loader ou versão', title=slug)
        return

    return target

def get_primary_jar(compatible_version: dict, slug: str):
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

def resolve_dependencies(compatible_version: dict, ctx: Context):
    dir_mods = ctx.dir_mods

    if not dir_mods.is_dir():
        logger.error(f'{dir_mods} não é um diretório')
        return
    
    dependencies = compatible_version.get('dependencies', [])

    if len(dependencies) == 0:
        return

    # obter o slug do mod pai de onde essa dependencia vem
    # é diferente do id da dependencia em si. é obtido só pra mostrar no log
    parent_slug = get_slug_from_id(compatible_version.get('project_id'))

    # baixar cada dependência
    for d in dependencies:
        if not d.get('dependency_type') == 'required':
            continue

        # obtém o slug em vez do id pra ser mais legível por humanos
        # isso deve ser feito pq geralmente as dependencias ficam listadas com id nos dados da api
        project_id = d.get('project_id')
        dependency_slug = get_slug_from_id(project_id)

        resolve_project_downloading(dependency_slug, ctx, is_dependency_for=parent_slug)

def get_slug_from_id(project_id: str):
    """
    obtém o slug (indentificador legível)
    a partir do id (identificador aleatório) de um projeto
    """

    data = get_project_data(project_id, section=None)
    return data.get('slug')

def resolve_project_downloading(slug: str, ctx: Context, is_dependency_for: str | None = None):
    version = ctx.version
    loader = ctx.loader
    dir_mods = ctx.dir_mods
    dir_predownloaded = ctx.dir_predownloaded

    response = get_project_data(slug)
    if not response:
        logger.warning('pulando, erro ao obter os dados do projeto', title=slug)
        return
    compatible_version = get_compatible_version(response, slug, ctx)
    if not compatible_version:
        return
    resolve_dependencies(compatible_version, ctx)
    url, filename = get_primary_jar(compatible_version, slug)

    # tentar obter um arquivo já existente antes de tentar baixar
    found = None
    for f in dir_predownloaded.rglob('*.jar'):
        if f.name == filename:
            found = f
    
    # definir argumentos pro log
    nerdfont_icon = logger.DEFAULT_NERDFONT_ICON
    dependency_label = None
    if is_dependency_for is not None:
        dependency_label = f'é uma dependência de {is_dependency_for}'
        nerdfont_icon = '󰯁'

    # se tiver achado uma cópia já baixada, só copi aela pro diretório de mods
    # se não baixa pelo modrinth
    if found is not None:
        logger.success('mod já baixado encontrado', title=slug, nerdfont_icon=nerdfont_icon, details=dependency_label)
        shutil.copy2(found, dir_mods)
    else:
        # baixar o .jar triggando um spinner pro carregamento do download
        with logger.spinner(title=slug, details=dependency_label):
            dest = download_jar(url, filename, dir_mods)
        
        # copiar pro diretório de já baixados pra não precisar baixar de novo
        subdown = None
        if not is_dependency_for:
            subdown = dir_predownloaded / version
        else:
            subdown = dir_predownloaded / version / 'dependencies'
        subdown.mkdir(exist_ok=True, parents=True)
        shutil.copy2(dest, subdown)

def load_modpack(modpack: Path, delete_previous: bool = True):
    dir_mods = DOTMINECRAFT / 'mods'
    dir_mods.mkdir(exist_ok=True, parents=True)

    # deletar todos os mods presentes na .minecraft/mods, se especificado
    if delete_previous:
        logger.info('deletando todos os mods anteriores')
        
        for f in dir_mods.rglob('*.jar'):
            f.unlink()
            
        logger.success('mods deletados')

    # obter os dados do modpack
    with modpack.open('r', encoding='utf-8') as mp:
        data = json.load(mp)

    version = data.get('version')
    loader = data.get('loader')
    slugs = data.get('slugs')
    
    ctx = Context(
        version=version,
        loader=loader,
        dir_mods=dir_mods,
        dir_predownloaded=Path('./downloads')
    )

    # dados extras pro log
    logger.modpack_init(
        name=modpack.stem, count=len(slugs),
        version=version, loader=loader)

    # baixar pela internet ou pegar arquivos já existentes
    # que correspondem a cada mod especificado no arquivo
    for s in slugs:
        resolve_project_downloading(s, ctx)

#download_from_modrinth('sodium', '1.20.1', 'fabric')
load_modpack(Path('./modpacks/visuals.json'))
#load_modpack(Path('./modpacks/construction.json'))