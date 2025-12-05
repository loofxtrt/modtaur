from pathlib import Path
from dataclasses import dataclass, field
import json

DOTMINECRAFT = Path.home() / '.minecraft'
API_BASE = 'https://api.modrinth.com/v2'
HEADERS = {"User-Agent": "modtaur/0.1"}

@dataclass
class File():
    url: str
    filename: str
    primary: bool

@dataclass
class Dependency():
    #version_id: str # pode ser usado pra mais precisão, mas até agora não foi implementado
    project_id: str
    dependency_type: str

@dataclass
class Project():
    game_versions: list[str]
    id: str
    slug: str
    project_type: str
    #title: str
    #description: str
    loaders: list[str]

@dataclass
class Version():
    project_id: str # id do projeto pai que contém a versão
    id: str         # id da versão
    game_versions: list[str]
    loaders: list[str]
    #name: str
    #version_number: str
    version_type: str
    files: list[File]
    dependencies: list[Dependency]
    #changelog: str

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

        resolved:
            slugs de mods que já foram resolvidos pelo software
            isso evita ciclos de dependência, fazendo o mesmo mod não ser visitado duas vezes
    """

    version: str
    loader: str
    dir_predownloaded: Path
    dir_mods: Path
    dir_resourcepacks: Path
    dir_cache_version_lists: Path
    resolved: set[str] = field(default_factory=set)

def read_json(file: Path):
    try:
        with file.open('r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def write_json(file: Path, data):
    try:
        with file.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception:
        pass