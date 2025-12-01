from pathlib import Path
import json

from .constants import DOTMINECRAFT, Context
from .modrinth import resolve_project_downloading
from . import logger

def load_modpack(modpack: Path, delete_previous: bool = True):
    dir_mods = DOTMINECRAFT / 'mods'
    dir_resourcepacks = DOTMINECRAFT / 'resourcepacks'
    
    minecraft_dirs = [dir_mods, dir_resourcepacks]

    for d in minecraft_dirs:
        # ter certeza de que os diretórios principais existem
        d.mkdir(exist_ok=True, parents=True)

        # limpar eles se assim especificado
        if delete_previous:
            logger.info('deletando todos os mods anteriores')

            for f in d.rglob('*'):
                f.unlink()

            logger.success('mods deletados')

    # obter os dados do modpack
    with modpack.open('r', encoding='utf-8') as mp:
        data = json.load(mp)

    version = data.get('version')
    loader = data.get('loader')
    mods = data.get('mods')
    resourcepacks = data.get('resourcepacks')

    ctx = Context(
        version=version,
        loader=loader,
        dir_mods=dir_mods,
        dir_resourcepacks=dir_resourcepacks,
        dir_predownloaded=Path('./downloads')
    )

    # dados extras pro log
    logger.modpack_init(
        name=modpack.stem, version=version, loader=loader,
        mod_count=len(mods), resourcepack_count=len(resourcepacks)
    )

    # baixar pela internet ou pegar arquivos já existentes
    # que correspondem a cada mod especificado no arquivo
    for m in mods:
        resolve_project_downloading(m, 'mod', ctx)
    for r in resourcepacks:
       resolve_project_downloading(r, 'resourcepack', ctx)

#load_modpack(Path('./modpacks/visuals.json'))