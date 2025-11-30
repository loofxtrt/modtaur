from contextlib import contextmanager

from rich.console import Console
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner

# cores são baseadas na cor da logo do modrinth, com hue mudado
LEVEL_COLORS = {
    'info': '#1b8fd9',
    'success': '#1bd96a', # cor original
    'error': '#d91b47',
    'warning': '#d9bd1b'
}
DEFAULT_NERDFONT_ICON = '󱍔'

def _title_appender(text: Text, title: str, style: str, title_max: int | None = 20):
    if title_max:
        if len(title) > title_max:
            title = title[:-1]
            title += '…' # ellipsis em vez de pontos pra ocupar menos espaço
        title = title.ljust(title_max + 8)

    text.append(title, style=style)
    text.append(' ')

def _log(msg, level, title: str | None = None, nerdfont_icon: str = DEFAULT_NERDFONT_ICON):
    # 󱍔 󱌣 󰖷 󰒓 󰗝 󱀥 os ícones são nf-md
    style = f'bold {LEVEL_COLORS.get(level)}'

    text = Text()
    text.append(nerdfont_icon, style)
    text.append(' ')
    if title:
        _title_appender(text, title, style)
    text.append(msg)
    
    console = Console()
    console.print(text)

def success(msg, title: str | None = None, nerdfont_icon: str = DEFAULT_NERDFONT_ICON):
    _log(msg, 'success', title=title, nerdfont_icon=nerdfont_icon)

def info(msg, title: str | None = None, nerdfont_icon: str = DEFAULT_NERDFONT_ICON):
    _log(msg, 'info', title=title, nerdfont_icon=nerdfont_icon)

def warning(msg, title: str | None = None, nerdfont_icon: str = DEFAULT_NERDFONT_ICON):
    _log(msg, 'warning', title=title, nerdfont_icon=nerdfont_icon)

def error(msg, title: str | None = None, nerdfont_icon: str = DEFAULT_NERDFONT_ICON):
    _log(msg, 'error', title=title, nerdfont_icon=nerdfont_icon)

@contextmanager
def spinner(msg = 'downloading...', title: str | None = None):
    style = f'bold {LEVEL_COLORS.get('success')}'

    text = Text()
    if title:
        _title_appender(text, title, style)
    text.append(msg)

    spinner = Spinner('dots', text, style=style)
    console = Console()
    with Live(spinner, refresh_per_second=10, console=console) as live:
        try:
            yield
        finally:
            final = Text()
            final.append(DEFAULT_NERDFONT_ICON, style)
            final.append(' ')
            if title:
                _title_appender(final, title, style)
            final.append('download concluído')
            live.update(final)

def modpack_init(name: str, count: int, version: str, loader: str):
    # logger especial só pro momento em que uma leitura de modpack começa
    style = f'bold {LEVEL_COLORS.get('success')}'
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