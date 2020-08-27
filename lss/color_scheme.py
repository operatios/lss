from lss.constants import Category

COLOR_SCHEME = {
    Category.FILE: ('green', None, []),
    Category.DIRECTORY: ('blue', None, ['bold']),
    Category.SYMLINK: ('black', 'cyan', ['underline']),
    Category.REPARSE_POINT: ('black', 'cyan', ['underline']),
    Category.BROKEN_LINK: ('black', 'red', []),
    Category.ARCHIVE: ('red', None, []),
    Category.EXECUTABLE: ('red', None, ['bold']),
    Category.CODE: ('magenta', None, []),
    Category.IMAGE: ('yellow', None, []),
    Category.VIDEO: ('yellow', None, ['bold']),
    Category.AUDIO: ('yellow', None, []),
}

SIZE = {
    'start_color': '#00ff00',
    'end_color': '#ff0000',
    'maxsize': 1073741824,
    'thresholds': [0.0625, 0.125, 0.1875, 0.25, 0.375, 0.5, 0.75, 1]
}
