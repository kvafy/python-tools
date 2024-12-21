# Tool for hiding multimedia files, so that they don't get annoyingly auto-picked up by the OS
# media scanner and polute the feed.

import argparse
import datetime
import os
import os.path
import platform
import random
import re
import subprocess
import sys

from functools import partial
from typing import Callable, Iterator


HIDDEN_EXTENSION = 'hdn'
MEDIA_EXTENSIONS = {'3gp', 'asf', 'avi', 'flv', 'webm', 'mkv', 'mp4', 'mpeg', 'mpg', 'mov', 'wmv'}


def find_files(
        path : str,
        file_filter : Callable[[os.DirEntry], bool],
        recurse : bool) -> Iterator[os.DirEntry]:
    # Support specifying a concrete file instead of a directory. Must do this via
    # a limited `os.scandir` to get the file as an `os.DirEntry`.
    if os.path.isfile(path):
        file_filter2 = lambda entry: file_filter(entry) and entry.name == os.path.basename(path)
        yield from find_files(os.path.dirname(path), file_filter2, recurse=False)
        return
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file() and file_filter(entry):
                yield entry
            if entry.is_dir() and recurse:
                yield from find_files(entry.path, file_filter, recurse)

def rename_files_keeping_time(
        files : Iterator[os.DirEntry],
        renamer : Callable[[str], str],
        **kvargs) -> None:
    file_mutator = partial(rename_file_keeping_time, renamer=renamer, **kvargs)
    list(map(file_mutator, files))

def rename_file_keeping_time(
        file : os.DirEntry,
        renamer : Callable[[str], str],
        dry_run : bool,
        verbose : bool) -> None:
    orig_path = file.path
    orig_stat = file.stat()
    new_path = renamer(file.path)
    if dry_run:
        print(f"Simulating rename of '{orig_path}'")
        return
    if verbose: print(f"Renaming '{orig_path}'")
    os.rename(orig_path, new_path)
    os.utime(new_path, times=(orig_stat.st_atime, orig_stat.st_mtime))

def retime_files(
        files : list[os.DirEntry],
        cutoff_time : datetime.datetime,
        spread_secs : int,
        **kvargs):
    offsets = (random.random() * (-spread_secs) for _ in files)
    new_times = [cutoff_time + datetime.timedelta(milliseconds=1000*off) for off in offsets]

    # Preserve the relative time order of files after re-timing.
    sorted_files = sorted(files, key=file_max_time)
    sorted_new_times = sorted(new_times)

    for file, new_base_time in zip(sorted_files, sorted_new_times):
        retime_file(file, new_base_time, **kvargs)

def retime_file(file : os.DirEntry, new_base_time : datetime.datetime, dry_run : bool, verbose : bool):
    small_pos_delta = lambda: datetime.timedelta(milliseconds=random.randrange(100, 1000))

    (cur_ctime, cur_mtime, cur_atime) = file_times(file)
    # Determine which times need to be shifted backwards.
    new_ctime = new_base_time                 if (cur_ctime > cutoff_time) else cur_ctime
    new_mtime = new_ctime + small_pos_delta() if (cur_mtime > cutoff_time) else cur_mtime
    new_atime = new_mtime + small_pos_delta() if (cur_atime > cutoff_time) else cur_atime

    change_log = []
    if cur_ctime != new_ctime: change_log.append(f"ctime {cur_ctime} -> {new_ctime}")
    if cur_mtime != new_mtime: change_log.append(f"mtime {cur_mtime} -> {new_mtime}")
    if cur_atime != new_atime: change_log.append(f"atime {cur_atime} -> {new_atime}")

    if dry_run:
        print(f"Simulating retiming of '{file.path}':{'\n* ' + '\n* '.join(change_log)}")
        return

    if verbose: print(f"Retiming '{file.path}':{'\n* ' + '\n* '.join(change_log)}")
    if cur_ctime != new_ctime:
        # Creation time cannot be manipulated by Python directly. Using os-specific tricks.
        if platform.system() == 'Windows':
            # https://superuser.com/questions/292630/how-can-i-change-the-timestamp-on-a-file
            run_powershell_expecting_success(
                f"$(Get-Item '{powershell_escape_apostrophes(file.path)}').CreationTime = $(Get-Date '{new_ctime}')")
        else:
            print(f"Warning for '{file.name}': ctime change is not implemented for this OS", file=sys.stderr)
    if (cur_mtime != new_mtime) or (cur_atime != new_atime):
        os.utime(file.path, times=(new_atime.timestamp(), new_mtime.timestamp()))
    log_file_times(file, desc='after retime') # debug only

def powershell_escape_apostrophes(s : str) -> str:
    return s.replace("'", "''")

def run_powershell_expecting_success(cmd : str):
    ret = subprocess.call(["powershell", "-Command", cmd])
    if ret != 0:
        raise IOError(f"Error: PowerShell command '{cmd}' failed with error code {ret}.")

def print_file_times(files : Iterator[os.DirEntry], base_dir : str):
    def normalize_path(e : os.DirEntry):
        result = os.path.relpath(e.path, base_dir)
        if len(result) > 80:
            result = result[:75] + "[...]"
        return result

    files = sorted(files, key=lambda f: f.path)
    if not files:
        return

    max_norm_path_len = max(map(lambda f: len(normalize_path(f)), files))
    fmt_time = "%Y-%m-%d %H:%M:%S.%f"
    fmt_head = f"{{name:^{max_norm_path_len}}} | {{ctime:^26}} | {{mtime:^26}} | {{atime:^26}}"
    fmt_body = f"{{name:<{max_norm_path_len}}} | {{ctime:{fmt_time}}} | {{mtime:{fmt_time}}} | {{atime:{fmt_time}}}"
    print(fmt_head.format(name='File', ctime='ctime', mtime='mtime', atime='atime'))
    for file in files:
        (ctime, mtime, atime) = file_times(file)
        print(fmt_body.format(name=normalize_path(file), ctime=ctime, mtime=mtime, atime=atime))

def log_file_times(file : os.DirEntry, desc : str = ''):
    to_time = lambda x: datetime.datetime.fromtimestamp(x)
    stat = os.stat(file.path)  # Grab fresh stat.
    info = f" ({desc})" if desc else ""
    print(f"Times of '{file.name}'{info}:")
    print(f"  - st_atime = {to_time(stat.st_atime)}")
    print(f"  - st_mtime = {to_time(stat.st_mtime)}")
    print(f"  - st_ctime = {to_time(stat.st_ctime)}")

def file_extension(entry : os.DirEntry) -> str:
    ext_mo = re.match(r".*\.([^.]+)", entry.name)
    return ext_mo and ext_mo.group(1).lower()

def file_times(entry : os.DirEntry) -> tuple[datetime.datetime]:
    ctime = datetime.datetime.fromtimestamp(entry.stat().st_ctime)
    mtime = datetime.datetime.fromtimestamp(entry.stat().st_mtime)
    atime = datetime.datetime.fromtimestamp(entry.stat().st_atime)
    return (ctime, mtime, atime)

def file_max_time(entry : os.DirEntry) -> datetime.datetime:
    # Windows: Explorer shows `mtime` (TODO: ignore `atime`?).
    # Mac: Finder shows "Date added" which isn't an attribute of the file entry.
    # Linux: TODO
    return max(*file_times(entry))

def add_file_ext(name : str, ext : str):
    return f"{name}.{ext}"

def remove_file_ext(name : str, ext : str):
    return name.removesuffix(f".{ext}")

def parse_ceil_spec(spec : str):
    # Example: "2024-08-01 15:36 - 0:30"
    p = re.compile(r"""(?ix)     # Verbose, ignore case
        (?P<cutoff>
          \d{4}-\d{1,2}-\d{1,2}  # Date part
          \s+
          \d{1,2}:\d{1,2})       # Time part
        \s*-\s*
        (?P<spread_hh>\d{1,2}):(?P<spread_mm>\d{1,2})
    """)
    mo = p.fullmatch(spec)
    if not mo:
        raise ValueError()
    cutoff_time = datetime.datetime.strptime(mo.group('cutoff'), '%Y-%m-%d %H:%M')
    spread_secs = 60 * (int(mo.group('spread_mm')) + 60 * int(mo.group('spread_hh')))
    return (cutoff_time, spread_secs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='hdn',
        description='Swiss army knife for manipulating files based on various criteria.')
    parser.add_argument('-r', '--recursive', action='store_true')
    parser.add_argument('-s', '--simulate', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--hide-mm', action='store_true', help='hide multi-media files')
    parser.add_argument('--unhide-mm', action='store_true', help='unhide multi-media files')
    parser.add_argument('--print-time', action='store_true', help='print timestamps of files')
    parser.add_argument('--ceil-time', type=parse_ceil_spec, help='Set a ceiling on file times.'
                        ' E.g. "2024-08-01 12:00 - 0:30" will shift times of all files to be no'
                        ' no later than 12:00, spread out within 30 minutes, preserving relative'
                        ' order.')
    parser.add_argument('dir', default='.')

    args = parser.parse_args()

    kwargs = {'dry_run': args.simulate, 'verbose': args.verbose}

    if args.hide_mm or args.unhide_mm:
        if args.hide_mm:
            file_filter = lambda entry: file_extension(entry) in MEDIA_EXTENSIONS
            renamer = partial(add_file_ext, ext=HIDDEN_EXTENSION)
        elif args.unhide_mm:
            file_filter = lambda entry: file_extension(entry) == HIDDEN_EXTENSION
            renamer = partial(remove_file_ext, ext=HIDDEN_EXTENSION)
        files_it = find_files(args.dir, file_filter, args.recursive)
        rename_files_keeping_time(files_it, renamer, **kwargs)

    elif args.ceil_time:
        (cutoff_time, spread_secs) = args.ceil_time
        file_filter = lambda entry: cutoff_time < file_max_time(entry)
        files_it = find_files(args.dir, file_filter, args.recursive)
        retime_files(list(files_it), cutoff_time, spread_secs, **kwargs)

    elif args.print_time:
        file_filter = lambda _: True  
        files_it = find_files(args.dir, file_filter, args.recursive)
        print_file_times(files_it, args.dir)
