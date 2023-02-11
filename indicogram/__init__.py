from clld_corpus_plugin.models import Text
from clld_document_plugin import decorate_gloss_string
from clld_markdown_plugin import comma_and_list
from clld_morphology_plugin.models import POS, Lexeme, Morph, Morpheme, Wordform
from pyramid.config import Configurator

from indicogram import interfaces, models


def get_kwarg(string, kwargs):
    return kwargs.get(string, [None])[0]


table_dic = {
    "MorphsetTable": [Morpheme, "morpheme"],
    "FormTable": [Wordform, "wordform"],
    "LexemeTable": [Lexeme, "lexeme"],
}


def render_lfts(req, objid, table, session, **kwargs):
    model, route = table_dic[table]
    if "ids" in kwargs:
        ids = kwargs["ids"][0].split(",")
        return comma_and_list(
            [render_lfts(req, unit_id, table, session) for unit_id in ids]
        )
    unit = session.query(model).filter(model.id == objid).first()
    url = req.route_url(route, id=objid, **kwargs)
    with_translation = "no_translation" not in kwargs
    md_str = f"*[{unit.name}]({url})*"
    translation = get_kwarg("translation", kwargs)
    if with_translation:
        meanings = [
            decorate_gloss_string(
                x.meaning.name,
                decoration=lambda x: f"<span class='smallcaps'>{x}</span>",
            )
            for x in unit.meanings
        ]
        if translation:
            meanings = [decorate_gloss_string(translation)]
        md_str += f" ‘{', '.join(meanings)}’"
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
            "MorphTable": {
                "route": "morph",
                "model": Morph,
                "decorate": lambda x: f"*{x}*",
            },
            "TextTable": {
                "route": "text",
                "model": Text,
                "decorate": lambda x: f"'{x}'",
            },
            "PhonemeTable": {
                "route": "phoneme",
                "model": models.Phoneme,
                "decorate": lambda x: f"/{x}/",
            },
            "POSTable": {"route": "pos", "model": POS},
            "FormTable": {
                "route": "wordform",
                "model": Wordform,
                "decorate": lambda x: f"*{x}*",
            },
        },
        "renderer_map": {
            "MorphsetTable": render_lfts,
            "FormTable": render_lfts,
            "LexemeTable": render_lex,
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
    return config.make_wsgi_app()
