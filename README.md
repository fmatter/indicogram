# InDiCoGram

Interactive digital corpus-based grammar.

![License](https://img.shields.io/github/license/fmatter/indicogram)

This is a [CLLD](https://clld.org/) app serving a digital grammar, combining a corpus with descriptive prose.
The heavy lifting is done by these plugins:

* [clld-morphology-plugin](https://github.com/fmatter/clld-morphology-plugin)
* [clld-corpus-plugin](https://github.com/fmatter/clld-corpus-plugin)
* [clld-markdown-plugin](https://github.com/clld/clld-markdown-plugin)
* [clld-document-plugin](https://github.com/fmatter/clld-document-plugin)

The only components provided by the app itself are:

* a very simple `Phoneme` model
* some [configuration](indicogram/__init__.py) for `clld-markdown-plugin`

The app, including the default [database initialization script](indicogram/scripts/initializedb.py) is designed to be compatible with CLDF datasets created from [FLEx](https://software.sil.org/fieldworks/) with [cldflex](https://github.com/fmatter/cldflex) and with [lingdocs](https://fl.mt/lingdocs)-generated markdown.

There's [a step-by-step tutorial](https://fl.mt/digital-grammar-tutorial) for FLEx > CLDF > lingdocs > CLLD.

Setup:

1. fork, clone, or download
2. create a virtual environment (suggested)
3. `pip install -e .[dev]`
4. `clld initdb development.ini --cldf /path/to/your/cldf/metadata.json`
5. `pserve development.ini`

## Changelog

### 2023-03-06
* restructured table navigation
* more colors

### 2023-02-23
* glossing abbreviations

### 2023-02-20
* added topics (referencing sections)

### 2023-02-20
* using [cldf-ldd](https://pypi.org/project/cldf-ldd/)
* better init script
* fixed gloss formatting