from pathlib import Path
import json

DOTMINECRAFT = Path.home() / '.minecraft'

def set_modpack(
    modpack: dict,
    instructions: dict,
    jar_database: Path,
    dotminecraft: Path = DOTMINECRAFT
    ):
    version = modpack.get('version')
    mods = modpack.get('mods')
    resourcepacks = modpack.get('resourcepacks')
    
    