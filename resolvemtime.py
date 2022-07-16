import argparse
import ast
import os
import glob
import collections
import itertools
import logging
import sys

SpecEntry = collections.namedtuple('SpecEntry', ['value', 'attrs'])


def make_parser():
    parser = argparse.ArgumentParser(
        description=('Check if the oldest modification time in targets is '
                     'newer than the latest modification time in '
                     'dependencies. There should be one ore more targets and '
                     'zero or more dependencies. When there\'s no dependency, '
                     'the program always returns zero.'),
        epilog=('Return code: zero - the predicate above is fault; non-zero - '
                'the predicate is true. Specifically, 1 -- no error occurs, '
                '2 - error occurs (e.g. file/directory not found).'))
    parser.add_argument('spec', type=os.path.normpath, help='the spec file')
    parser.add_argument('--files', action='store_true', help='list files only')
    return parser


def read_spec(filename):
    with open(filename) as infile:
        spec = ast.literal_eval(infile.read())
    return spec


def yield_entries(list_spec, default_attrs: str):
    for entry in list_spec:
        if isinstance(entry, str):
            yield SpecEntry(entry, default_attrs)
        else:
            attrs, value = entry
            yield SpecEntry(value, attrs + default_attrs)


def resolve_entry(entry: SpecEntry):
    logger = logging.getLogger(resolve_entry.__name__)
    filenames = []
    value = entry.value
    if 'u' in entry.attrs:
        value = os.path.expanduser(value)
    if 'v' in entry.attrs:
        value = os.path.expandvars(value)
    filenames.append(value)
    if 'g' in entry.attrs and '@' not in entry.attrs:
        filenames.extend(glob.glob(filenames.pop()))
    elif 'g' in entry.attrs:
        logger.info('`g` skipped on "%s" since it\'s redirected by `@`',
                    entry.value)
    if 'r' in entry.attrs and '@' not in entry.attrs:
        filenames2 = []
        while filenames:
            value = filenames.pop()
            if os.path.isdir(value):
                for root, _, files in os.walk(value):
                    for name in files:
                        filenames2.append(os.path.join(root, name))
            else:
                filenames2.append(value)
        filenames = filenames2
        del filenames2
    elif 'r' in entry.attrs:
        logger.info('`r` skipped on "%s" since it\'s redirected by `@`',
                    entry.value)
    if '@' in entry.attrs:
        assert len(filenames) == 1, filenames
        reffilename = filenames.pop()
        new_attrs = entry.attrs.replace('@', '')
        with open(reffilename) as infile:
            for line in infile:
                line = line.strip()
                if line:
                    new_entry = SpecEntry(line, new_attrs)
                    filenames.extend(resolve_entry(new_entry))
    return filenames


def resolve_list_spec(list_spec, default_attrs: str):
    return itertools.chain.from_iterable(
        resolve_entry(e) for e in yield_entries(list_spec, default_attrs))


def resolve_targets_mtime(targets, default_attrs):
    mtime = float('inf')
    for e in resolve_list_spec(targets, default_attrs):
        mtime = min(mtime, os.path.getmtime(e))
    return mtime


def resolve_dependencies_mtime(dependencies, default_attrs):
    mtime = -float('inf')
    for e in resolve_list_spec(dependencies, default_attrs):
        mtime = max(mtime, os.path.getmtime(e))
    return mtime


def main():
    logging.basicConfig(format='resolvemtime: %(levelname)s: %(message)s')
    args = make_parser().parse_args()
    logger = logging.getLogger()
    try:
        spec = read_spec(args.spec)
    except OSError as err:
        logger.error('OSError %s occurs while reading spec "%s"', err,
                     args.spec)
        return 2
    default_attrs = spec.get('defaults', '')
    try:
        targets = spec['targets']
    except KeyError:
        logger.error('spec must contain a key named "targets", which should '
                     'be a list of string/2-tuple entries')
        return 2
    if not targets:
        logger.error('targets must contain at least one entry')
        return 2
    dependencies = spec.get('dependencies', [])
    if args.files:
        print('=== targets ===')
        for e in resolve_list_spec(targets, default_attrs):
            print(e)
        print()
        print('=== dependencies ===')
        for e in resolve_list_spec(dependencies, default_attrs):
            print(e)
        return 0

    if not dependencies:
        return 0
    try:
        t_mtime = resolve_targets_mtime(targets, default_attrs)
        d_mtime = resolve_dependencies_mtime(dependencies, default_attrs)
    except OSError as err:
        logger.error('OSError %s occurs while resolving mtime', err)
        return 2
    return 0 if d_mtime > t_mtime else 1


if __name__ == '__main__':
    sys.exit(main())
