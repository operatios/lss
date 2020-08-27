import colorsys
import json
import os

from lss.constants import Category
from lss.color_scheme import COLOR_SCHEME, SIZE

# These two are generated at runtime
SIZE_STEPS = None
SIZE_GRADIENT = None

COLORS = {
    'black': 30,
    'red': 31,
    'green': 32,
    'yellow': 33,
    'blue': 34,
    'magenta': 35,
    'cyan': 36,
    'white': 37
}

BG_COLORS = {
    'black': 40,
    'red': 41,
    'green': 42,
    'yellow': 43,
    'blue': 44,
    'magenta': 45,
    'cyan': 46,
    'white': 47
}

RESET = 0
ATTRIBUTES = {
    'bold': 1,
    'dim': 2,
    'italic': 3,
    'underline': 4,
    'blink': 5,
    'reverse': 7,
    'hidden': 8
}

# 16 colors
ANSI = '\033[%dm'
# 256 colors, unused
FG08 = '\033[38;5;%dm'
BG08 = '\033[48;5;%dm'
# RGB
FG24 = '\033[38;2;%d;%d;%dm'
BG24 = '\033[48;2;%d;%d;%dm'


def init(long_listing=False):
    """If we're not using ConEmu or Windows Terminal we have to call
    os.system('color') to enable colors and eliminate line wrapping
    """
    is_conemu = 'CONEMUDIR' in os.environ
    is_windows_terminal = 'WT_SESSION' in os.environ
    if os.name == 'nt' and not (is_conemu or is_windows_terminal):
        os.system('color')

    lss_path = os.path.dirname(os.path.realpath(__file__))
    custom_path = os.path.join(lss_path, 'lss_custom.json')

    if os.path.exists(custom_path):
        with open(custom_path) as file:
            custom = json.load(file)
            for key, value in custom['categories'].items():
                COLOR_SCHEME[Category[key.upper()]] = value
            for key, value in custom['size'].items():
                SIZE[key] = value

    # Generate gradients only if we're using long listing mode
    if long_listing:
        global SIZE_STEPS
        global SIZE_GRADIENT

        SIZE_STEPS = [SIZE['maxsize'] * i for i in SIZE['thresholds']]
        start_rgb = tuple(i/255 for i in hex_to_rgb(SIZE['start_color']))
        end_rgb = tuple(i/255 for i in hex_to_rgb(SIZE['end_color']))

        SIZE_GRADIENT = list(
            make_gradient(start_rgb, end_rgb, len(SIZE_STEPS) - 1)
        )


def sizecolor(size):
    if size >= SIZE_STEPS[-1]:
        return SIZE_GRADIENT[-1]

    for i, step in enumerate(SIZE_STEPS):
        if size < step:
            return SIZE_GRADIENT[i]


def fmt_cat(string, category):
    return fmt(string, *COLOR_SCHEME[category])


def fmt(string, fg=None, bg=None, attributes=None):
    if not attributes:
        attributes = tuple()

    if isinstance(fg, str):
        fg_fmt = ANSI % COLORS[fg] if fg else ''
    else:
        fg_fmt = FG24 % (fg[0], fg[1], fg[2]) if fg else ''

    if isinstance(bg, str):
        bg_fmt = ANSI % BG_COLORS[bg] if bg else ''
    else:
        bg_fmt = BG24 % (bg[0], bg[1], bg[2]) if bg else ''

    attrs_fmt = ''.join(ANSI % ATTRIBUTES[attr] for attr in attributes)
    return '%s%s%s%s%s' % (bg_fmt, fg_fmt, attrs_fmt, string, ANSI % RESET)


def hex_to_rgb(code):
    code = code.lstrip('#')
    if len(code) != 6:
        raise ValueError

    return int(code[:2], 16), int(code[2:4], 16), int(code[4:], 16)


def make_gradient(start_rgb, end_rgb, steps):
    start = colorsys.rgb_to_hsv(*start_rgb)
    end = colorsys.rgb_to_hsv(*end_rgb)
    reverse = False

    if end[0] < start[0]:
        start, end = end, start
        reverse = True

    dist_forward = end[0] - start[0]
    dist_backwards = start[0] + (1 - end[0])

    if dist_backwards < dist_forward:
        step_h = -dist_backwards / steps
    else:
        step_h = dist_forward / steps

    step_s = (end[1] - start[1]) / steps
    step_v = (end[2] - start[2]) / steps

    step_iter = range(steps+1) if not reverse else reversed(range(steps+1))
    for i in step_iter:
        h = start[0] + step_h * i
        if h < 0:
            h = 1 + h
        s = start[1] + step_s * i
        v = start[2] + step_v * i

        yield tuple(i * 255 for i in colorsys.hsv_to_rgb(h, s, v))
