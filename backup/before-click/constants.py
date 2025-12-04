from pathlib import Path
from dataclasses import dataclass

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
        
        dir_resourcepacks:
            ~/.minecraft/resourcepacks
    """

    version: str
    loader: str
    dir_predownloaded: Path
    dir_mods: Path
    dir_resourcepacks: Path