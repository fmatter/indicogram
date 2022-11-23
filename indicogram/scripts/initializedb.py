import collections
import csv
import itertools
import logging
import sys

import colorlog
from clld.cliutil import Data, bibtex2source
from clld.db.meta import DBSession
from clld.db.models import common
from clld.lib import bibtex
from clld_corpus_plugin.models import (
    SentenceSlice,
    SentenceTag,
    Speaker,
    SpeakerSentence,
    Tag,
    Text,
    TextSentence,
    TextTag,
)
from clld_document_plugin.models import Document
from clld_morphology_plugin.models import (
    POS,
    FormMeaning,
    FormSlice,
    Inflection,
    Lexeme,
    LexemeLexemePart,
    LexemeMorphemePart,
    Meaning,
    Morph,
    Morpheme,
    MorphemeMeaning,
    Wordform,
    Wordform_files,
)
from clldutils.color import qualitative_colors
from clldutils.misc import nfilter
from pycldf import Sources
from clldutils import licenses

csv.field_size_limit(sys.maxsize)

handler = colorlog.StreamHandler(None)
handler.setFormatter(
    colorlog.ColoredFormatter("%(log_color)s%(levelname)-7s%(reset)s %(message)s")
)
log = logging.getLogger(__name__)
log.propagate = False
log.addHandler(handler)

from pathlib import Path

import pandas as pd
from slugify import slugify

import indicogram
from indicogram import models


def listify(obj):
    if not isinstance(obj, list):
        return [obj]
    return obj


# license_dic = {
#     "creativecommons.org/licenses/by/4.0": {
#         "license_icon": "cc-by.png",
#         "license_name": "Creative Commons Attribution 4.0 International License",
#     },
#     "creativecommons.org/licenses/by-sa/4.0": {
#         "license_icon": "cc-by-sa.png",
#         "license_name": "Creative Commons Attribution-ShareAlike 4.0 International",
#     },
# }

cc_icons = [
    "cc-by-nc-nd",
    "cc-by-nc-sa",
    "cc-by-nc",
    "cc-by-nd",
    "cc-by-sa",
    "cc-by",
    "cc-zero",
]


def get_license_data(license_tag, small=False):
    license = licenses.find(license_tag)
    if not license:
        log.warning(f'Could not interpret license "{license_tag}"')
        return None
    license_dict = {"license_name": license.name}
    license_tag = license.id.replace("CC0", "cc-zero")
    for icon in cc_icons:
        if "license_icon" in license_dict:
            continue
        if icon.upper() in license.id:
            if small:
                license_dict["license_icon"] = icon + "-small.png"
            else:
                license_dict["license_icon"] = icon + ".png"
    return license_dict


def main(args):

    cldf = args.cldf  # passed in via --cldf
    cldf_tables = list(cldf.components.keys()) + [
        str(x.url) for x in cldf.tables
    ]  # a list of tables in the dataset
    recommended_tables = [
        x + "Table"
        for x in [
            "Language",
            "Contributor",
            "Parameter",
            "Morphset",
            "Morph",
            "Form",
            "Examples",
            "Chapter",
        ]
    ]

    def check_table(tablename):
        if tablename not in cldf_tables and tablename in recommended_tables:
            log.warning(f"No {tablename} found")
        return tablename in cldf_tables

    demo_data = []
    data = Data()
    dataset = data.add(
        common.Dataset,
        indicogram.__name__,
        id=indicogram.__name__,
        name=cldf.properties[
            "dc:title"
        ],  # all the dc:X data should be in your CLDF dataset
        domain=cldf.properties.get("dc:identifier", "://none").split("://")[1],
        license=cldf.properties["dc:license"],
        jsondata=get_license_data(cldf.properties["dc:license"], small=False),
        publisher_name="",
        publisher_place="",
        publisher_url="",
    )

    if check_table("ContributorTable"):  # the author(s)
        log.info("Contributors")
        for contributor in cldf.iter_rows("ContributorTable"):
            if dataset.contact is None and contributor["Email"] is not None:
                dataset.contact = contributor["Email"]

            new_cont = data.add(
                common.Contributor,
                contributor["ID"],
                id=contributor["ID"],
                name=contributor["Name"],
                email=contributor["Email"],
                url=contributor["Url"],
            )
            dataset.editors.append(
                common.Editor(
                    contributor=new_cont, ord=contributor["Order"], primary=True
                )
            )

    log.info("Sources")
    for rec in bibtex.Database.from_file(cldf.bibpath):
        data.add(common.Source, rec.id, _obj=bibtex2source(rec))

    if check_table("LanguageTable"):
        log.info("Languages")
        for lang in cldf.iter_rows("LanguageTable"):
            data.add(
                common.Language,
                lang["ID"],
                id=lang["ID"],
                name=lang["Name"],
                latitude=lang["Latitude"],
                longitude=lang["Longitude"],
            )

    if check_table("ParameterTable"):
        log.info("Meanings")
        for meaning in cldf.iter_rows("ParameterTable"):
            data.add(Meaning, meaning["ID"], id=meaning["ID"], name=meaning["Name"])

    if check_table("PhonemeTable"):
        log.info("Phonemes")
        phoneme_dict = {}
        for pnm in cldf.iter_rows("PhonemeTable"):
            phoneme_dict[pnm["Name"]] = pnm["ID"]
            data.add(models.Phoneme, pnm["ID"], id=pnm["ID"], name=pnm["Name"])

    if check_table("POSTable"):
        log.info("Parts of speech")
        for pos in cldf.iter_rows("POSTable"):
            data.add(
                POS,
                pos["ID"],
                id=pos["ID"],
                name=pos["Name"],
                description=pos["Description"],
            )

    if check_table("MorphsetTable"):
        log.info("Morphemes")
        for morpheme in cldf.iter_rows("MorphsetTable"):
            meanings = listify(
                morpheme["Parameter_ID"]
            )  # todo: some uncertainty here about whether a form can have multiple meanings or not
            new_morpheme = data.add(
                Morpheme,
                morpheme["ID"],
                id=morpheme["ID"],
                name=morpheme["Name"],
                language=data["Language"][morpheme["Language_ID"]],
                description=" / ".join(data["Meaning"][x].name for x in meanings),
                comment=morpheme["Comment"],
            )
            for meaning in meanings:
                data.add(
                    MorphemeMeaning,
                    f"{morpheme['ID']}-{meaning}",
                    id=f"{morpheme['ID']}-{meaning}",
                    morpheme=new_morpheme,
                    meaning=data["Meaning"][meaning],
                )

    if check_table("MorphTable"):
        log.info("Morphs")
        for morph in cldf.iter_rows("MorphTable"):
            data.add(
                Morph,
                morph["ID"],
                id=morph["ID"],
                name=morph["Name"],
                language=data["Language"][morph["Language_ID"]],
                morpheme=data["Morpheme"][morph["Morpheme_ID"]],
                description=" / ".join(
                    data["Meaning"][x].name
                    for x in listify(morph["Parameter_ID"])  # todo uncertainty
                ),
            )

    if check_table("FormTable"):
        log.info("Wordforms")
        for form in cldf.iter_rows("FormTable"):
            meanings = [
                data["Meaning"][x].name for x in listify(form["Parameter_ID"])
            ]  # todo: some uncertainty here about whether a form can have multiple meanings or not
            new_form = data.add(
                Wordform,
                form["ID"],
                id=form["ID"],
                name=form["Form"].replace("-", "").replace("∅", "").replace("Ø", ""),
                segmented=form["Form"],
                language=data["Language"][form["Language_ID"]],
                description=" / ".join(meanings),
            )

            for meaning in listify(form["Parameter_ID"]):
                data.add(
                    FormMeaning,
                    f"{form['ID']}-{meaning}",
                    form=new_form,
                    meaning=data["Meaning"][meaning],
                )
        demo_data.append(f"[](FormTable#cldf:{new_form.id}) is a nice word.")

    if check_table("FormSlices"):
        log.info("Form slices")
        for f_slice in cldf.iter_rows("FormSlices"):
            morph = data["Morph"][f_slice["Morph_ID"]]
            morpheme = morph.morpheme
            morpheme_meaning_id = f"{morpheme.id}-{f_slice['Morpheme_Meaning']}"
            form = data["Wordform"][f_slice["Form_ID"]]
            form_meaning_id = f"{form.id}-{f_slice['Form_Meaning']}"

            new_slice = data.add(
                FormSlice,
                f_slice["ID"],
                form=form,
                morph=morph,
                morpheme_meaning=data["MorphemeMeaning"][morpheme_meaning_id],
                form_meaning=data["FormMeaning"][form_meaning_id],
            )
            if f_slice["Index"]:
                new_slice.index = int(
                    f_slice["Index"]
                )  # todo this should be specified in the CLDF metadata
            else:
                log.info(f_slice)

    if check_table("TextTable"):
        log.info("Texts")
        for text in cldf.iter_rows("TextTable"):
            data.add(
                Text,
                text["ID"],
                id=text["ID"],
                name=text["Title"],
                description=text["Description"],
                text_metadata=text["Metadata"],
            )

    if check_table("SpeakerTable"):
        log.info("Speakers")
        for spk in cldf.iter_rows("SpeakerTable"):
            data.add(Speaker, spk["ID"], id=spk["ID"], name=spk["Abbreviation"])

    if check_table("ExampleTable"):
        log.info("Examples")
        for ex in cldf.iter_rows("ExampleTable"):
            ex["Analyzed_Word"] = ["" if x is None else x for x in ex["Analyzed_Word"]]
            ex["Gloss"] = ["" if x is None else x for x in ex["Gloss"]]
            new_ex = data.add(
                common.Sentence,
                ex["ID"],
                id=ex["ID"],
                name=ex["Primary_Text"],
                description=ex["Translated_Text"],
                analyzed="\t".join(ex["Analyzed_Word"]),
                gloss="\t".join(ex["Gloss"]),
                language=data["Language"][ex["Language_ID"]],
                comment=ex["Comment"],
            )
            if check_table("SpeakerTable"):
                data.add(
                    SpeakerSentence,
                    ex["ID"],
                    sentence=new_ex,
                    speaker=data["Speaker"][ex["Speaker_ID"]],
                )
            if ex.get("Text_ID", None) is not None:
                data.add(
                    TextSentence,
                    ex["ID"],
                    sentence=new_ex,
                    text=data["Text"][ex["Text_ID"]],
                    record_number=ex["Record_Number"],
                    phrase_number=ex.get("Phrase_Number", None)
                )
            elif len(ex.get("Source", [])) > 0:
                bibkey, pages = Sources.parse(ex["Source"][0])
                source = data["Source"][bibkey]
                DBSession.add(
                    common.SentenceReference(
                        sentence=new_ex, source=source, key=source.id, description=pages
                    )
                )
        demo_data.append(
            f"""As you can see in <a class="exref" example_id="{new_ex.id}"></a>, it's all there for you to use.\n[](ExampleTable#cldf:{new_ex.id})"""
        )

    if check_table("ExampleSlices"):
        log.info("Sentence slices")
        for sf in cldf.iter_rows("ExampleSlices"):
            if sf["Form_ID"] + "-" + sf["Parameter_ID"] not in data["FormMeaning"]:
                log.warning(
                    "This sentence slice's form ID is not associated with a meaning"
                )
                log.warning(sf)
                continue
            data.add(
                SentenceSlice,
                sf["ID"],
                form=data["Wordform"][sf["Form_ID"]],
                sentence=data["Sentence"][sf["Example_ID"]],
                index=int(sf["Index"]),
                form_meaning=data["FormMeaning"][
                    sf["Form_ID"] + "-" + sf["Parameter_ID"]
                ],
            )

    if check_table("ChapterTable"):
        log.info("Documents")
        chapters = {}
        for chapter in cldf.iter_rows("ChapterTable"):
            if chapter["ID"] == "landingpage":
                dataset.description = chapter["Description"]
            else:
                ch = data.add(
                    Document,
                    chapter["ID"],
                    id=chapter["ID"],
                    name=chapter["Name"],
                    description=chapter["Description"],
                    meta_data={},
                )
                if chapter["Number"] is not None:
                    ch.chapter_no = int(chapter["Number"])
                    ch.order = chr(int(chapter["Number"]) + 96)
                    chapters[ch.chapter_no] = ch
                else:
                    ch.order = "z"
        for nr, chapter in chapters.items():
            if 1 < nr:
                chapter.preceding = chapters[nr - 1]
    if not dataset.description:
        dataset.description = (
            f"Welcome to your fresh new CLLD grammar! "
            "To replace this text, add a chapter with the ID `landingpage` to your `ChapterTable`. "
            "If you don't have a `ChapterTable` yet, you can use [pylingdocs](https://pylingdocs.readthedocs.io/) "
            "or [cldfviz](https://github.com/cldf/cldfviz/) and [cldfbench](https://cldfbench.readthedocs.io) to do so. "
            "Here's some examples of what you can do with these tools:\n\n"
            + "\n".join(demo_data)
        )


def prime_cache(args):
    """If data needs to be denormalized for lookup, do that here.
    This procedure should be separate from the db initialization, because
    it will have to be run periodically whenever data has been updated.
    """
