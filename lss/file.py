import datetime
import functools
import dataclasses
import stat
import pathlib
import os

from lss.constants import Category, EXTENSION_TO_CATEGORY


@dataclasses.dataclass
class File:
    dir_entry: object

    @functools.cached_property
    def name(self):
        # Path('.').name is ''
        if not self.dir_entry.name:
            return '.'

        # Any of Path('..'), Path('../..'), etc.
        if self.dir_entry.name == '..':
            return str(self.dir_entry.resolve())

        return self.dir_entry.name

    @functools.cached_property
    def size(self):
        return self.stat.st_size

    @functools.cached_property
    def size_human_readable(self):
        """Uses kibi (1024) instead of kilo (1000): KiB, MiB ..."""
        size = self.size

        if size < 1024:
            return '%d' % size

        for unit in ('', 'K', 'M', 'G', 'T', 'P', 'E', 'Z'):
            if size < 1024:
                if size < 9:
                    return '%.1f%s' % (size, unit)
                return '%.0f%s' % (size, unit)
            size /= 1024

        return '%.1f%s' % (size, 'Y')

    @functools.cached_property
    def extension(self):
        return os.path.splitext(self.name)[1].lower()

    @functools.cached_property
    def real_path(self):
        return os.path.realpath(self.dir_entry)

    @functools.cached_property
    def relative_path(self):
        return os.path.relpath(self.dir_entry)

    @functools.cached_property
    def is_dir(self):
        if isinstance(self.dir_entry, pathlib.Path):
            return self.stat.st_mode & stat.S_IFDIR
        return self.dir_entry.is_dir(follow_symlinks=False)

    @functools.cached_property
    def is_symlink(self):
        return self.dir_entry.is_symlink()

    @functools.cached_property
    def attributes(self):
        """Windows file attributes"""
        return self.stat.st_file_attributes

    @functools.cached_property
    def filemode(self):
        return stat.filemode(self.stat.st_mode)

    @functools.cached_property
    def is_reparse(self):
        if os.name == 'posix':
            return False

        # Symlinks also have the REPARSE_POINT attribute
        # but reparse points != symlinks
        return bool(
            self.attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
            and not self.is_symlink
        )

    @functools.cached_property
    def is_broken(self):
        """Checks if symlink or a reparse point is broken"""
        if not self.is_symlink and not self.is_reparse:
            return False
        return not os.path.exists(self.real_path)

    @functools.cached_property
    def target(self):
        """Returns symlink/reparse point target path"""
        if not self.is_symlink and not self.is_reparse:
            return None

        relative_pointer = os.path.relpath(self.real_path)
        if relative_pointer.startswith('..'):
            return self.real_path

        return relative_pointer

    @functools.cached_property
    def last_modified_ts(self):
        """Returns timestamp of last file modification"""
        return self.stat.st_mtime

    @functools.cached_property
    def last_modified_str(self):
        """Returns string representation of when the file was last modified
           For example: "May  4 06:55", "Apr 20 13:37"
        """
        date = datetime.datetime.fromtimestamp(self.last_modified_ts)
        month = date.strftime('%B')
        day = date.strftime('%d')
        time = date.strftime('%H:%M')
        if day[0] == '0':
            day = day.replace('0', ' ', 1)
        return '%s %s %s' % (month[:3], day, time,)

    @functools.cached_property
    def stat(self):
        """Returns the appropriate dir_entry.stat based on its type"""
        if isinstance(self.dir_entry, pathlib.Path):
            # We need lstat if we're using pathlib to detect reparse points
            return self.dir_entry.lstat()
        return self.dir_entry.stat(follow_symlinks=False)

    @functools.cached_property
    def parent(self):
        """Must only be used if File is created from Path (when using globs)"""
        return File(self.dir_entry.parent)

    def unwrap_parents(self):
        """For `a/b/c/file` yields (c, b, a)"""
        if isinstance(self.dir_entry, os.DirEntry):
            for parent in reversed(self.relative_path.split(os.sep)[:-1]):
                yield parent
        else:
            cur_par = self.parent
            while cur_par.name != '.':
                yield cur_par
                cur_par = cur_par.parent

    @functools.cached_property
    def hidden(self):
        """Checks if filename starts with a '.'
        If on Windows, also checks whether file attributes are set to hidden
        """
        hidden = self.name[0] == '.'
        if os.name == 'nt':
            return hidden or self.attributes & stat.FILE_ATTRIBUTE_HIDDEN
        return hidden

    @functools.cached_property
    def category(self):
        """Used for sorting by category and choosing the appropriate color"""
        if self.is_broken:
            return Category.BROKEN_LINK
        if self.is_symlink:
            return Category.SYMLINK
        if self.is_reparse:
            return Category.REPARSE_POINT
        if self.is_dir:
            return Category.DIRECTORY

        return EXTENSION_TO_CATEGORY.get(self.extension, Category.FILE)
