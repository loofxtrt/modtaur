from constants import DOTMINECRAFT, Context

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
    mods = data.get('mods')
    
    ctx = Context(
        version=version,
        loader=loader,
        dir_mods=dir_mods,
        dir_predownloaded=Path('./downloads')
    )

    # dados extras pro log
    logger.modpack_init(
        name=modpack.stem, count=len(mods),
        version=version, loader=loader)

    # baixar pela internet ou pegar arquivos já existentes
    # que correspondem a cada mod especificado no arquivo
    for m in mods:
        resolve_project_downloading(m, ctx)