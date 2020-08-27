# lss
**lss** is a cross-platform implementation of `ls` written in Python

![image](https://raw.githubusercontent.com/operatios/lss/master/images/lss.png)

# Table of Contents
- [Why](#why)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Customization](#customization)
- [Limitations](#limitations)

# Why
Unlike other implementations of ls (and WSL's ls), **lss** supports Windows file attributes and reparse points. 

Files that have the hidden attribute set are properly recognized as hidden.

# Features
- Eye candy (RGB Colors, Nerd Fonts)
- Glob patterns: `*.py`, `**/*`, `**/*.png`
- Blazingly fast tree output
- Easily customizable
- Zero dependencies

# Installation
    pip install lss

# Usage
`lss`, `lss --sort=size`, `lss -a --tree`, `lss **/*.flac`

Flags and their description:

      -h, --help            show this help message and exit
      -a, --all             do not ignore hidden files
      -l, --long-listing    use a long listing format
      -t, --tree            list contents of directories in a tree-like format
      -b, --bytes           with -l: print size in bytes
      -f, --filemode        with -l: print file mode
      --sort {size,time,extension,category}
                            sort by WORD instead of name
      -s {S,t,X,c}          shorthand for --sort
      -c AMOUNT, --columns AMOUNT
                            set maximum amount of columns
      -r, --reverse         reverse file order
      -q QUOTE, --quote QUOTE
                            add value as a quote for filenames that contain a space
      --col-sep AMOUNT      set amount of whitespace between
                            columns
      --no-colors           disable colors
      --no-icons            disable icons
      --no-targets          do not print symlink targets

# Customization
Put `lss_custom.json` in your `site_packages/lss` directory

Check out [lss_custom.json](https://github.com/operatios/lss/blob/master/lss_custom.json) for more details

# Limitations
- On Linux you need to add quotes to your glob patterns `"**/*"`
- Broken reparse points stop recursive globbing (limitation of Python's pathlib)
