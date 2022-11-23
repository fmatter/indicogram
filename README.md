# clld-grammar-template
This is a skeleton for a [CLLD](https://clld.org/) app serving a digital grammar, combining a corpus with descriptive prose.
The heavy lifting is done by these plugins:

* [clld-morphology-plugin](https://github.com/fmatter/clld-morphology-plugin)
* [clld-corpus-plugin](https://github.com/fmatter/clld-corpus-plugin)
* [clld-markdown-plugin](https://github.com/clld/clld-markdown-plugin)
* [clld-document-plugin](https://github.com/fmatter/clld-document-plugin)

The only components provided by the skeleton are:

* a very simple `Phoneme` model
* some [configuration](indicogram/__init__.py) for `clld-markdown-plugin`

The app, including a pre-made [database initialization script](indicogram/scripts/initializedb.py) is designed to be compatible with CLDF datasets created from [FLEx](https://software.sil.org/fieldworks/) with [cldflex](https://github.com/fmatter/cldflex).

`clld initdb development.ini --cldf /path/to/your/cldf/metadata.json`