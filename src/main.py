from pathlib import Path

from src.load import load_modpack

#download_from_modrinth('sodium', '1.20.1', 'fabric')
load_modpack(Path('./modpacks/visuals.json'))
#load_modpack(Path('./modpacks/construction.json'))