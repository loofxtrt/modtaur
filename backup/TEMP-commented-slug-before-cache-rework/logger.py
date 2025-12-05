from contextlib import contextmanager

from rich.console import Console
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner

# cores são baseadas na cor da logo do modrinth, com hue mudado
LEVEL_COLORS = {
    'info':    ['#1b8fd9', 'blue'  ],
    'success': ['#1bd96a', 'green' ], # cor original
    'error':   ['#d91b47', 'red'   ],
    'warning': ['#d9bd1b', 'yellow'],
    'debug':   ['#1bb9d9', 'cyan'  ]
}
# ICON_PACKS = {
#     'outlined': {
#         'tool': '󰗝',
#         'cube': '󰆧'
#     },
#     'solid': {
#         'tool': '󱍔'
#         'cube': '󰆦'
#     }
# }
DEFAULT_NERDFONT_ICON = '󱍔'
USE_CUSTOM_COLORS = False
SHOW_DEBUG = True

def _get_level_color(level: str, custom: bool = True):
    """
    args:
        level:
            chave a ser procurado no mapa de cores
            ela retorna uma tupla com uma cor customizada
            e uma cor padrão do terminal

        custom:
            define se a cor obtida vai ser uma customizada
            ou uma cor padrão
    """

    index = 0 if custom else 1
    color_list = LEVEL_COLORS.get(level)
    return color_list[index]

def _title_appender(text: Text, title: str, style: str, title_max: int | None = 20):
    if title_max:
        if len(title) > title_max:
            title = title[:-1]
            title += '…' # ellipsis em vez de pontos pra ocupar menos espaço
        title = title.ljust(title_max + 8)

    text.append(title, style=style)
    text.append(' ')

def _icon_appender(text: Text, icon: str, style: str):
    text.append(icon, style=style)
    text.append(' ')

def _details_appender(text: Text, details: str, color: str):
    text.append(' ')
    text.append(details, color)

def _log(
    msg, level,
    title: str | None = None,
    details: str | None = None,
    nerdfont_icon: str = DEFAULT_NERDFONT_ICON,
    ):
    if level.lower() == 'debug' and not SHOW_DEBUG:
        return

    # 󱍔 󱌣 󰖷 󰒓 󰗝 󱀥 os ícones são nf-md
    color = _get_level_color(level, USE_CUSTOM_COLORS)
    style = f'bold {color}'

    # formatar a mensagem adicionando o ícone
    # título, a mensagem em si, e detalhes
    text = Text()
    _icon_appender(text, nerdfont_icon, style)
    if title: _title_appender(text, title, style)
    text.append(msg)
    if details: _details_appender(text, details, color)
 
    console = Console()
    console.print(text)

def debug(msg, **kwargs):
    _log(msg, 'debug', nerdfont_icon='󰃤', **kwargs)

def success(msg, **kwargs):
    _log(msg, 'success', **kwargs)

def info(msg, **kwargs):
    _log(msg, 'info', **kwargs)

def warning(msg, **kwargs):
    _log(msg, 'warning', **kwargs)

def error(msg, **kwargs):
    _log(msg, 'error', **kwargs)

@contextmanager
def spinner(msg = 'iniciando download...', title: str | None = None, details: str | None = None):
    color = _get_level_color('success', USE_CUSTOM_COLORS)
    style = f'bold {color}'

    def _resolve_title(text: Text):
        if title:
            _title_appender(text, title, style)

    def _resolve_details(text: Text):
        if details:
            _details_appender(text, details, color)

    def _resolve_icon(text: Text):
        _icon_appender(text, DEFAULT_NERDFONT_ICON, style)    

    # mensagem enquanto o spinner está em andamento
    while_downloading = Text()
    _resolve_title(while_downloading)
    while_downloading.append(msg)
    _resolve_details(while_downloading)

    # criar o spinner
    spinner = Spinner('dots', while_downloading, style=style)
    console = Console()
    
    with Live(spinner, refresh_per_second=10, console=console) as live:
        try:
            yield
        finally:
            # muda o texto de um spinner pra um estático depois de finalizar o download
            # o ícone é adicionado pra tomar o lugar que antes era ocupado pelo spinner
            after_downloaded = Text()
            _resolve_icon(after_downloaded)
            _resolve_title(after_downloaded)
            after_downloaded.append('download concluído')
            _resolve_details(after_downloaded)

            live.update(after_downloaded)

def modpack_init(name: str, mod_count: int, resourcepack_count: int, version: str, loader: str):
    # logger especial só pro momento em que uma leitura de modpack começa
    mod_count = str(mod_count)
    resourcepack_count = str(resourcepack_count)

    style = f'bold {_get_level_color('success', USE_CUSTOM_COLORS)}'
    
    text = Text()
    text.append('iniciando o carregamento de ')
    text.append(f'{mod_count}', style)
    text.append(' mods e ')
    text.append(f'{resourcepack_count}', style)
    text.append(' resourcepacks do modpack ')
    text.append(name, style)
    text.append(' pra versão ')
    text.append(version, style)
    text.append(' usando ')
    text.append(loader, style)

    _log(text, 'success', nerdfont_icon='󰒓')