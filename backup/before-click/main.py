from pathlib import Path
import json

from .constants import DOTMINECRAFT, Context
from .modrinth import resolve_project_downloading
from . import logger

def load_modpack(
    modpack: Path,
    delete_previous: bool = True,
    apply_mods: bool = True,
    apply_resourcepacks: bool = True
    ):
    minecraft_dirs = []

    if apply_mods:
        dir_mods = DOTMINECRAFT / 'mods'
        minecraft_dirs.append(dir_mods)

    if apply_resourcepacks:
        dir_resourcepacks = DOTMINECRAFT / 'resourcepacks'
        minecraft_dirs.append(dir_resourcepacks)

    if len(minecraft_dirs) == 0:
        return

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
    if apply_mods:
        for m in mods:
            resolve_project_downloading(m, 'mod', ctx)
    if apply_resourcepacks:
        for r in resourcepacks:
            resolve_project_downloading(r, 'resourcepack', ctx)

load_modpack(Path('./modpacks/visuals.json'), apply_resourcepacks=False)