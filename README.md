# `pyresolvemtime`, Makefile-like modification time resolver

## Usage

```
Check if the oldest modification time in targets is newer than the latest
modification time in dependencies. There should be one ore more targets and zero or
more dependencies. When there's no dependency, the program always returns zero.

positional arguments:
  spec        the spec file

optional arguments:
  -h, --help  show this help message and exit
  --files     list files only

Return code: zero - the predicate above is fault; non-zero - the predicate is true.
Specifically, 1 -- no error occurs, 2 - error occurs (e.g. file/directory not
found).
```

## Example spec file

```python
# this line is comment
{
    #"defaults": "uvgr",  # default attributes
    "targets":
    [
        "file",
        ("u", "~/.bashrc"),  # user expansion
        ("v", "$HOME/.zshrc"),  # variable expansion
        ("g", "*.csv"),  # glob expansion, relative to parent dir of build file
        ("r", "dir"),  # recurse into directories
        ("@gr", "filename"),  # reference external list of file, where `@`
                              # redirects the effect of `g`, `r` to each non-empty
                              # line of "filename"
    ],
    "dependencies":
    [
        # ...
    ],
}
```
