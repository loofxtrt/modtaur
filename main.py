from pathlib import Path
import shutil
import json

DOTMINECRAFT = Path.home() / '.minecraft'

def normalize_jar_file(file: Path | str):
    normalized = str(file)
    if not normalized.endswith('.jar'):
        normalized += '.jar'

    if isinstance(file, str):
        normalized = Path(normalized)

    return normalized

def set_modpack(
    modpack: dict,
    instructions: dict,
    jars_directory: Path,
    dotminecraft: Path = DOTMINECRAFT
    ):
    loader = modpack.get('loader')
    version = modpack.get('version')
    mods = modpack.get('mods')
    #resourcepacks = modpack.get('resourcepacks')

    for m in mods:
        m = normalize_jar_file(m)
        dest = dotminecraft / 'mods' / m
        for j in jars_directory.rglob('*.jar'):
            if j.name == m:
                src = j

        shutil.copy2(src, dest)
    
def download_from_modrinth(mod_id: str, version: str, loader: str = 'fabric'):
    url = f'https://modrinth.com/mod/{mod_id}?version={version}&loader={loader}'