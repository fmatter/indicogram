from cldf_ldd.components import (
    LexemeTable,
    MorphemeTable,
    MorphTable,
    POSTable,
    TextTable,
    WordformTable,
)
from clld_corpus_plugin.models import Text
from clld_document_plugin import decorate_gloss_string
from clld_document_plugin.models import Document
from clld_markdown_plugin import comma_and_list
from clld_morphology_plugin.models import POS, Lexeme, Morph, Morpheme, Wordform, Form
from pyramid.config import Configurator
from clld.web.util.helpers import link
from indicogram import interfaces, models

boolmap = {"False": False, "True": True}


def get_kwarg(string, kwargs, bool=False, default=False):
    if not bool:
        return kwargs.get(string, [None])[0]
    if string in kwargs:
        return boolmap[kwargs[string][0]]
    return default


table_dic = {
    MorphemeTable["url"]: [Morpheme, "morpheme"],
    WordformTable["url"]: [Wordform, "wordform"],
    LexemeTable["url"]: [Lexeme, "lexeme"],
    MorphTable["url"]: [Morph, "morph"],
    "FormTable": [Form, "form"],
}


def render_lfts(req, objid, table, session, **kwargs):
    model, route = table_dic[table]
    if "ids" in kwargs:
        ids = kwargs.pop("ids")[0].split(",")
        return comma_and_list(
            [render_lfts(req, unit_id, table, session, **kwargs) for unit_id in ids]
        )
    unit = session.query(model).filter(model.id == objid).first()
    url = req.route_url(route, id=objid, **kwargs)
    with_translation = get_kwarg("with_translation", kwargs, bool=True, default=True)
    with_language = "with_language" in kwargs
    with_source = "with_source" in kwargs
    md_str = f"*[{unit.name}]({url})*"
    if with_language:
        md_str = unit.language.name + " " + md_str
    translation = get_kwarg("translation", kwargs)
    if not translation:
        translation = unit.description
    if with_translation:
        # meanings = [
        #     decorate_gloss_string(
        #         x.meaning.name,
        #         decoration=lambda x: f"<span class='smallcaps'>{x}</span>",
        #     )
        #     for x in unit.meanings
        # ]
        if translation:
            meanings = [
                decorate_gloss_string(
                    translation,
                    decoration=lambda x: f"<span class='smallcaps'>{x}</span>",
                )
            ]
        md_str += f" ‘{', '.join(meanings)}’"
    if with_source and unit.source:
        md_str += f" ({link(req, unit.source)})"
    return md_str


def render_lex(req, objid, table, session, **kwargs):
    unit = session.query(Lexeme).filter(Lexeme.id == objid).first()
    url = req.route_url("lexeme", id=objid, **kwargs)
    with_translation = "no_translation" not in kwargs
    md_str = f"<span class='smallcaps'>[{unit.name}]({url})</span>"
    if with_translation:
        meanings = [
            decorate_gloss_string(
                x, decoration=lambda x: f"<span class='smallcaps'>{x}</span>"
            )
            for x in [unit.description]
        ]
        md_str += f" ‘{', '.join(meanings)}’"
    return md_str


def main(global_config, **settings):
    """This function returns a Pyramid WSGI application."""
    settings["clld_markdown_plugin"] = {
        "model_map": {
            TextTable["url"]: {
                "route": "text",
                "model": Text,
                "decorate": lambda x: f"'{x}'",
            },
            "phonemes.csv": {
                "route": "phoneme",
                "model": models.Phoneme,
                "decorate": lambda x: f"/{x}/",
            },
            "chapters.csv": {
                "route": "document",
                "model": Document,
            },
            POSTable["url"]: {"route": "pos", "model": POS},
        },
        "renderer_map": {
            "FormTable": render_lfts,
            MorphTable["url"]: render_lfts,
            MorphemeTable["url"]: render_lfts,
            WordformTable["url"]: render_lfts,
            LexemeTable["url"]: render_lfts,
        },
        "extensions": [],
    }

    config = Configurator(settings=settings)
    config.include("clld.web.app")
    config.include("clld_corpus_plugin")
    config.include("clld_morphology_plugin")
    config.include("clld_markdown_plugin")
    config.include("clld_document_plugin")

    config.register_resource(
        "phoneme", models.Phoneme, interfaces.IPhoneme, with_index=True
    )

    config.add_page("description")
    config.add_page("corpus")
    config.add_page("morphosyntax")
    config.add_page("lexicon")

    return config.make_wsgi_app()
