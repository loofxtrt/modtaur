from rich.console import Console
from rich.text import Text

def _log(msg, level, title: str | None = None, title_max: int = 20, nerdfont_icon: str = '󱍔'):
    # cores são baseadas na cor da logo do modrinth, com hue mudado
    level_colors = {
        'info': '#1b8fd9',
        'success': '#1bd96a', # cor original,
        'error': '#d91b47',
        'warning': '#d9bd1b'
    }

    # 󱍔 󱌣 󰖷 󰒓 os ícones são nf-md
    color = level_colors.get(level)

    text = Text()
    text.append(nerdfont_icon, color)
    text.append(' ')
    if title:
        #title = title.ljust(30)
        #if not title.endswith(':'):
            #title += ':'

        if len(title) > title_max:
            title = title[:-1]
            title += '…' # ellipsis em vez de pontos pra ocupar menos espaço
        title = title.ljust(title_max + 4)

        text.append(title, style=f'bold {color}')
        text.append(' ')
    text.append(msg)
    
    console = Console()
    console.print(text)

def success(msg, title: str | None = None):
    _log(msg, 'success', title=title)

def info(msg, title: str | None = None):
    _log(msg, 'info', title=title)

def warning(msg, title: str | None = None):
    _log(msg, 'warning', title=title)

def error(msg, title: str | None = None):
    _log(msg, 'error', title=title)

def modpack_init(name: str, count: int, version: str, loader: str):
    # logger especial só pro momento em que uma leitura de modpack começa
    style = '#1bd96a bold'
    text = Text()
    text.append('iniciando o carregamento de ')
    text.append(str(count), style)
    text.append(' mods do modpack ')
    text.append(name, style)
    text.append(' pra versão ')
    text.append(version, style)
    text.append(' usando ')
    text.append(loader, style)
    _log(text, 'success', nerdfont_icon='󰒓')