from pathlib import Path

import click

from .modrinth import resolve_project_downloading, get_project, get_version_list
from .parser import get_compatible_version
from .utils import read_json, DOTMINECRAFT, Context, DotMinecraft
from . import logger

dir_mods = DOTMINECRAFT / 'mods'
dir_resourcepacks = DOTMINECRAFT / 'resourcepacks'

def _context_from_modpack_data(data: dict) -> Context:
    version = data.get('version')
    loader = data.get('loader')
    
    return Context(
        version=version,
        loader=loader,
        dotminecraft=DotMinecraft(),
        cache_root=Path('./cache'),
    )

def _normalize_json_path(file: Path | str) -> Path:
    stringfied = file
    
    if isinstance(file, Path):
        stringfied = str(file)

    if not stringfied.endswith('.json'):
        stringfied += '.json'
    
    return Path(stringfied)

def _is_modpack_valid(modpack: Path) -> bool:
    if not modpack.is_file():
        return False
    
    return True

@click.group
def modtaur_cli():
    pass

@modtaur_cli.command(name='verify')
@click.argument('modpack')
@click.option('--version', '-v')
@click.option('--loader', '-l')
def verify_compatiblity(modpack: str, version: str | None, loader: str | None):
    """
    verifica a compatibilidade dos mods de um modpack em relação a uma versão e loader

    args:
        version:
            1.21.8, 1.20.1 etc.

        loader:
            fabric, forge etc.

        ambos os argumentos a cima, se não especificados,
        o valor usado vai ser o que está dentro do modpack
    """
    
    logger.debug(modpack, title='verify')
    
    modpack = _normalize_json_path(modpack)

    if not _is_modpack_valid(modpack):
        return
    
    data = read_json(modpack)
    ctx = _context_from_modpack_data(data)
    if not version:
        version = ctx.version
    if not loader:
        loader = ctx.loader

    for m in data.get('mods'):
        proj = get_project(m)

        compatible = False
        if version in proj.game_versions and loader in proj.loaders:
            compatible = True

        details = f'versão {version} : loader {loader}'

        if not compatible:
            logger.error(f'incompatível', title=m, details=details)
        else:
            logger.success(f' compatível ', title=m, details=details)

@modtaur_cli.command(name='load')
@click.argument('modpack')
@click.option('--delete-previous', '-del', is_flag=True, default=True)
@click.option('--apply-mods', '-mod', is_flag=True, default=True)
@click.option('--apply-resourcepacks', '-res', is_flag=True, default=False)
def load_modpack(
    modpack: str,
    delete_previous: bool = True,
    apply_mods: bool = True,
    apply_resourcepacks: bool = False
    ):
    logger.debug(modpack, title='load')
    
    if not _is_modpack_valid(modpack):
        return
    
    # obter os dados do modpack
    modpack = _normalize_json_path(modpack)
    data = read_json(modpack)

    version = data.get('version')
    loader = data.get('loader')

    mods = data.get('mods', [])
    resourcepacks = data.get('resourcepacks', [])

    ctx = _context_from_modpack_data(data)
    dotminecraft = ctx.dotminecraft

    # manipulação de diretórios
    minecraft_dirs = []

    if apply_mods:
        minecraft_dirs.append(dotminecraft.mods)
    if apply_resourcepacks:
        minecraft_dirs.append(dotminecraft.resourcepacks)

    if len(minecraft_dirs) == 0:
        return

    # limpar os diretórios básicos se assim especificado
    for d in minecraft_dirs:
        if delete_previous:
            logger.info('deletando todos os mods anteriores')

            for f in d.rglob('*'):
                f.unlink()

            logger.success('mods deletados')

    # dados extras pro log
    logger.modpack_init(
        name=modpack.stem, version=version, loader=loader,
        mod_count=len(mods), resourcepack_count=len(resourcepacks)
    )

    # baixar pela internet ou pegar arquivos já existentes
    # que correspondem a cada mod especificado no arquivo
    if apply_mods:
        for m in mods:
            project = get_project(m)
            resolve_project_downloading(project, ctx)
    if apply_resourcepacks:
        for r in resourcepacks:
            project = get_project(r)
            resolve_project_downloading(project, ctx)

if __name__ == '__main__':
    modtaur_cli()

#load_modpack(Path('./modpacks/visuals.json'), apply_resourcepacks=False)