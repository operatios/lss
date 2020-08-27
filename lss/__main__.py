import argparse
import collections
import functools
import os
import pathlib
import sys

from lss import color, icons
from lss.file import File
from lss.constants import (
    Category,
    ENOENT,
    ENOTDIR,
    FALLBACK_TERMINAL_WIDTH,
    STOPITER
)


def prettify(file, args):
    pretty = file.name

    if args.quote:
        pretty = '%s%s%s' % (args.quote, pretty, args.quote)

    if not args.show_icons:
        return pretty

    if file.is_symlink or file.is_reparse:
        icon = icons.SYMLINK_DIR if file.is_dir else icons.SYMLINK_FILE

        if args.show_targets:
            arrow = '->' if not args.show_icons else icons.SYMLINK_PTR
            pretty = '%s %s %s' % (pretty, arrow, file.target)

    elif file.is_dir:
        icon = icons.DIR
    else:
        icon = icons.EXTENSIONS.get(file.extension, icons.FILE)

    return '%s %s' % (icon, pretty)


def colorize(file, args):
    if not args.show_colors:
        return prettify(file, args)
    return color.fmt_cat(prettify(file, args), file.category)


def get_terminal_width():
    try:
        return os.get_terminal_size().columns
    except OSError:
        return FALLBACK_TERMINAL_WIDTH


def get_files(pattern, return_hidden=False):
    if '*' in pattern:
        files = (File(path) for path in pathlib.Path().glob(pattern))
    else:
        try:
            files = (File(dir_entry) for dir_entry in os.scandir(pattern))
        except FileNotFoundError:
            print(ENOENT % pattern)
            sys.exit(2)  # ENOENT

    if not return_hidden:
        files = (file for file in files if not file.hidden)
    return files


# Change to @functools.cache once Python 3.9 releases
@functools.lru_cache(maxsize=None)
def get_row_col(i, rows):
    row = i % rows
    return row, (i-row) // rows


def format_rows(files, file_count, columns, terminal_width, args):
    if file_count % columns != 0:
        row_count = (file_count // columns) + 1
    else:
        row_count = file_count // columns

    rows = [[] for row in range(row_count)]
    column_widths = [0] * columns

    for i in range(file_count):
        _, col = get_row_col(i, row_count)
        name_length = len(prettify(files[i], args))

        if name_length > column_widths[col]:
            column_widths[col] = name_length

    row_width = sum(column_widths) + (len(column_widths) - 1) * args.col_sep
    if row_width >= terminal_width:
        return None

    for i in range(file_count):
        row, col = get_row_col(i, row_count)
        whitespace = ' ' * (column_widths[col] - len(prettify(files[i], args)))
        rows[row].append('%s%s' % (colorize(files[i], args), whitespace))

    return rows


def sort_files(files, args):
    # Files on Linux are not guaranteed to be sorted alphabetically
    if os.name == 'posix':
        files.sort(key=lambda x: x.name.lower())

    if args.sort in ('size', 'S'):
        files.sort(key=lambda x: x.size, reverse=True)
    elif args.sort in ('time', 't'):
        files.sort(key=lambda x: x.last_modified_ts, reverse=True)
    elif args.sort in ('extension', 'X'):
        files.sort(key=lambda x: x.extension)
    elif args.sort in ('category', 'c'):
        files.sort(key=lambda x: x.category)

    if args.reverse:
        files.reverse()


def process_files(files, args):
    sort_files(files, args)

    if args.long_listing or args.columns == 1:
        columns = 1
    else:
        terminal_width = get_terminal_width()
        file_count = len(files)
        columns = 2 if not args.columns else args.columns

    # If columns argument is set, we go backwards immediately
    going_backwards = bool(args.columns)
    while columns > 1:
        rows = format_rows(files, file_count, columns, terminal_width, args)
        if going_backwards and rows:
            break
        if not rows:
            going_backwards = True

        columns = columns * 2 if not going_backwards else columns - 1

    # Outputting files in a list
    if columns == 1:
        if args.long_listing:
            if args.bytes:
                sizes = [str(file.size) for file in files]
            else:
                sizes = [file.size_human_readable for file in files]
            size_align = len(max(sizes, key=len))

            for i in range(len(files)):
                size_s = sizes[i]
                ws_align = ' ' * (size_align - len(sizes[i]))

                if args.show_colors:
                    size_s = color.fmt(size_s, color.sizecolor(files[i].size))

                line = ['%s%s' % (ws_align, size_s),
                        files[i].last_modified_str,
                        colorize(files[i], args)]

                if args.filemode:
                    line.insert(0, files[i].filemode)

                print(' '.join(line))
        else:
            for file in files:
                print(colorize(file, args))

    # Outputting files in columns
    else:
        separator = ' ' * args.col_sep
        for row in rows:
            print(separator.join(row))


def process_glob(files, args):
    parents = collections.defaultdict(list)
    for file in files:
        parents[str(file.parent.dir_entry)].append(file)

    iterable = reversed(parents.items()) if args.reverse else parents.items()
    for parent_name, children in iterable:
        if not args.all:
            for child_file in children:
                if any(p.hidden for p in child_file.unwrap_parents()):
                    continue

        if parent_name != '.':
            print('%s:' % parent_name)

        process_files(children, args)


def process_tree(files, args, from_depths):
    sort_files(files, args)
    depth = len(list(files[0].unwrap_parents()))

    for file in files:
        is_last = file == files[-1]

        if file.is_dir and is_last:
            from_depths.discard(depth)
        elif file.is_dir:
            from_depths.add(depth)

        prefix = ''
        for i in range(depth):
            if i in from_depths:
                prefix += '│  '
            else:
                prefix += '   '

        if is_last:
            prefix += '└──'
        else:
            prefix += '├──'

        fmt_str = '%s%s' % (prefix, colorize(file, args))

        if not file.is_dir or file.is_reparse or file.is_symlink:
            print(fmt_str)

        if file.is_dir and not (file.is_reparse or file.is_symlink):
            try:
                dir_files = list(get_files(file.real_path, args.all))
                print(fmt_str)
                if dir_files:
                    process_tree(dir_files, args, from_depths)
            except PermissionError:
                print('%s %s' % (fmt_str, '[error opening dir]'))


def process_pattern(pattern, args):
    if args.tree:
        try:
            os.chdir(os.path.join(os.getcwd(), pattern))
        except FileNotFoundError:
            print(ENOENT % pattern)
            sys.exit(2)  # ENOENT
        except NotADirectoryError:
            print(ENOTDIR % pattern)
            sys.exit(20)  # ENOTDIR

        if args.show_colors:
            print(color.fmt_cat(pattern, Category.DIRECTORY))
        else:
            print(pattern)

        process_tree(list(get_files('.', args.all)), args, {0})

    elif '*' in pattern:
        generator = get_files(pattern, args.all)
        files = []
        while True:
            try:
                files.append(next(generator))
            # Broken reparse points encountered by Path().glob() raise OSError
            except OSError as ex:
                if ex.args[0] == 2:
                    print(STOPITER % pattern)
            except StopIteration:
                break

        process_glob(files, args)

    else:
        files = list(get_files(pattern, args.all))
        process_files(files, args)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('paths', nargs='*', default=tuple('.'))
    parser.add_argument(
        '-a', '--all',
        action='store_true',
        help='do not ignore hidden files'
    )
    parser.add_argument(
        '-l', '--long-listing',
        action='store_true',
        help='use a long listing format'
    )
    parser.add_argument(
        '-t', '--tree',
        action='store_true',
        help='list contents of directories in a tree-like format'
    )
    parser.add_argument(
        '-b', '--bytes',
        action='store_true',
        help='with -l: print size in bytes'
    )
    parser.add_argument(
        '-f', '--filemode',
        action='store_true',
        help='with -l: print file mode'
    )
    parser.add_argument(
        '--sort',
        choices=('size', 'time', 'extension', 'category'),
        help='sort by WORD instead of name'
    )
    parser.add_argument(
        '-s',
        dest='sort',
        choices=('S', 't', 'X', 'c'),
        help='shorthand for --sort'
    )
    parser.add_argument(
        '-c', '--columns',
        metavar='AMOUNT',
        type=int,
        help='set maximum amount of columns'
    )
    parser.add_argument(
        '-r', '--reverse',
        action='store_true',
        help='reverse file order'
    )
    parser.add_argument(
        '-q', '--quote',
        default='',
        help='add value as a quote for filenames that contain a space'
    )
    parser.add_argument(
        '--col-sep',
        help='set amount of whitespace between columns',
        metavar='AMOUNT',
        type=int,
        default=2
    )
    parser.add_argument(
        '--no-colors',
        action='store_false',
        dest='show_colors',
        help='disable colors'
    )
    parser.add_argument(
        '--no-icons',
        action='store_false',
        dest='show_icons',
        help='disable icons'
    )
    parser.add_argument(
        '--no-targets',
        action='store_false',
        dest='show_targets',
        help='do not print symlink targets'
    )

    args = parser.parse_args()

    if args.columns and args.columns < 1:
        print('--columns: amount should be >=1')
        sys.exit(-1)
    if args.col_sep < 0:
        print('--col-sep: amount should be >=0')
        sys.exit(-1)

    if not sys.stdout.isatty():
        args.columns = 1
        args.show_colors = False
        args.show_icons = False
        args.show_targets = False

    if args.show_colors:
        color.init(args.long_listing)

    for pattern in args.paths:
        if len(args.paths) > 1 and '*' not in pattern:
            print('%s:' % pattern)

        process_pattern(pattern, args)


if __name__ == '__main__':
    main()
