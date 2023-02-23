import csv
import logging
import sys

import colorlog
from clld.cliutil import Data, bibtex2source
from clld.db.meta import DBSession
from clld.db.models import common
from clld.lib import bibtex
import clld_corpus_plugin.models as corpus
import clld_document_plugin.models as doc
import clld_morphology_plugin.models as morpho
from clldutils import licenses
from pycldf import Sources

import indicogram
from slugify import slugify

csv.field_size_limit(sys.maxsize)

handler = colorlog.StreamHandler(None)
handler.setFormatter(
    colorlog.ColoredFormatter("%(log_color)s%(levelname)-7s%(reset)s %(message)s")
)
log = logging.getLogger(__name__)
log.propagate = False
log.addHandler(handler)


def listify(obj):
    if not isinstance(obj, list):
        return [obj]
    return obj


cc_icons = [
    "cc-by-nc-nd",
    "cc-by-nc-sa",
    "cc-by-nc",
    "cc-by-nd",
    "cc-by-sa",
    "cc-by",
    "cc-zero",
]

param_dict = {}


def generate_description(rec):
    return ", ".join([param_dict.get(x, x) for x in listify(rec["Parameter_ID"])])


def get_license_data(license_tag, small=False):
    if license_tag == None:
        return {}
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


tag_dic = {}


def tag_slug(tag):
    if tag not in tag_dic:
        tagslug = slugify(tag)
        suff = 1
        while f"{tagslug}-{suff}" in tag_dic.values():
            suff += 1
        tag_dic[tag] = f"{tagslug}-{suff}"
    return tag_dic[tag]


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

    def iter_table(tablename):
        if tablename[0] == tablename[0].lower():
            tablename = f"{tablename}.csv"
        if tablename in cldf_tables:
            log.info(tablename)
            for entry in cldf.iter_rows(tablename):
                yield entry
        # else:
        #     log.warning(f"Table '{tablename}' does not exist")

    def get_link(rec, field, datafield=None):
        if not datafield:
            datafield = field.replace("_ID", "")
        if field in rec and rec[field]:
            if isinstance(rec[field], list):
                return [data[datafield][x] for x in rec[field]]
            return data[datafield][rec[field]]
        return None

    demo_data = []
    data = Data()
    if "http" in cldf.properties.get("dc:identifier", ""):
        domain = cldf.properties.get("dc:identifier").split("://")[1]
    else:
        domain = "example.org/"

    def get_link(rec, field, datafield=None):
        if not datafield:
            datafield = field.replace("_ID", "")
        if field in rec and rec[field]:
            if isinstance(rec[field], list):
                return [data[datafield][x] for x in rec[field]]
            return data[datafield][rec[field]]
        return None

    dataset = data.add(
        common.Dataset,
        indicogram.__name__,
        id=indicogram.__name__,
        name=cldf.properties.get(
            "dc:title", "Unnamed dataset"
        ),  # all the dc:X data should be in your CLDF dataset
        domain=domain,
        license=cldf.properties.get("dc:license", None),
        jsondata=get_license_data(cldf.properties.get("dc:license", None), small=False),
        publisher_name="",
        publisher_place="",
        publisher_url="",
    )

    for contributor in iter_table("contributors"):
        if dataset.contact is None and contributor["Email"] is not None:
            dataset.contact = contributor["Email"]

        jsondata = {}
        if "Orcid" in contributor:
            jsondata["orcid"] = contributor["Orcid"]
        new_cont = data.add(
            common.Contributor,
            contributor["ID"],
            id=contributor["ID"],
            name=contributor["Name"],
            email=contributor["Email"],
            url=contributor["Url"],
            jsondata=jsondata,
        )
        dataset.editors.append(
            common.Editor(contributor=new_cont, ord=contributor["Order"], primary=True)
        )

    log.info("Sources")
    for rec in bibtex.Database.from_file(cldf.bibpath):
        data.add(common.Source, rec.id, _obj=bibtex2source(rec))

    for lang in iter_table("LanguageTable"):
        for lang in cldf.iter_rows("LanguageTable"):
            data.add(
                common.Language,
                lang["ID"],
                id=lang["ID"],
                name=lang["Name"],
                latitude=lang["Latitude"],
                longitude=lang["Longitude"],
            )

    for meaning in iter_table("ParameterTable"):
        param_dict[meaning["ID"]] = meaning["Name"]
        # data.add(Meaning, meaning["ID"], id=meaning["ID"], name=meaning["Name"])

    phoneme_dict = {}
    for pnm in iter_table("phonemes"):
        phoneme_dict[pnm["Name"]] = pnm["ID"]
        data.add(indicogram.models.Phoneme, pnm["ID"], id=pnm["ID"], name=pnm["Name"])

    for pos in iter_table("partsofspeech"):
        data.add(
            morpho.POS,
            pos["ID"],
            id=pos["ID"],
            name=pos["Name"],
            description=pos["Description"],
        )

    for wordform in iter_table("wordforms"):
        new_form = data.add(
            morpho.Wordform,
            wordform["ID"],
            id=wordform["ID"],
            language=data["Language"][wordform["Language_ID"]],
            name=wordform["Form"],
            description=generate_description(wordform),
            parts=wordform["Morpho_Segments"],
        )

    if "wordforms.csv" in cldf_tables:
        demo_data.append(
            f"[](FormTable#cldf:{new_form.id}) is one of my favorite [](LanguageTable#cldf:{new_form.language.id}) wordforms."
        )

    for morpheme in iter_table("morphemes"):
        data.add(
            morpho.Morpheme,
            morpheme["ID"],
            id=morpheme["ID"],
            name=morpheme["Name"],
            language=data["Language"][morpheme["Language_ID"]],
            description=generate_description(morpheme),
        )

    for morph in iter_table("morphs"):
        new_morph = data.add(
            morpho.Morph,
            morph["ID"],
            id=morph["ID"],
            language=data["Language"][morph["Language_ID"]],
            name=morph["Name"],
            description=generate_description(morph),
        )
        if morph["Name"].startswith("-"):
            new_morph.morph_type = "suffix"
        elif morph["Name"].endswith("-"):
            new_morph.morph_type = "prefix"
        elif "<" in morph["Name"]:
            new_morph.morph_type = "infix"
        else:
            new_morph.morph_type = "root"
        new_morph.morpheme = get_link(morph, "Morpheme_ID")

    for gloss in iter_table("glosses"):
        data.add(morpho.Gloss, gloss["ID"], id=gloss["ID"], name=gloss["Name"])

    for fslice in iter_table("wordformparts"):
        wf = data["Wordform"][fslice["Wordform_ID"]]
        morph = get_link(fslice, "Morph_ID")
        if fslice["Index"]:
            index = int(fslice["Index"])
        else:
            index = None
        new_formpart = data.add(
            morpho.WordformPart,
            fslice["ID"],
            id=fslice["ID"],
            morph=morph,
            form=wf,
            index=index,
        )
        for gloss_id in fslice["Gloss_ID"]:
            data.add(
                morpho.WordformPartGloss,
                fslice["ID"] + gloss_id,
                gloss=data["Gloss"][gloss_id],
                formpart=new_formpart,
            )

    for form in iter_table("forms"):
        data.add(
            morpho.Form,
            form["ID"],
            id=form["ID"],
            name=form["Form"],
            parts=form["Morpho_Segments"],
            description=generate_description(form),
            language=data["Language"][form["Language_ID"]],
        )

    for fslice in iter_table("formparts"):
        data.add(
            morpho.FormPart,
            fslice["ID"],
            wordform=data["Wordform"][fslice["Wordform_ID"]],
            form=data["Form"][fslice["Form_ID"]],
            index=int(fslice["Index"]),
        )

    for lexeme in iter_table("lexemes"):
        new_lexeme = data.add(
            morpho.Lexeme,
            lexeme["ID"],
            id=lexeme["ID"],
            name=lexeme["Name"],
            description=lexeme["Description"] or generate_description(lexeme),
            language=data["Language"][lexeme["Language_ID"]],
        )
        if "Paradigm_View" in lexeme and lexeme["Paradigm_View"]:
            x, y = lexeme["Paradigm_View"].split(";")
            x = x.split(",")
            y = y.split(",")
            new_lexeme.paradigm_x = x
            new_lexeme.paradigm_y = y

    for stem in iter_table("stems"):
        new_stem = data.add(
            morpho.Stem,
            stem["ID"],
            id=stem["ID"],
            name=stem["Name"],
            description=generate_description(stem),
            language=data["Language"][stem["Language_ID"]],
            parts=stem["Morpho_Segments"],
        )
        stem_glosses = get_link(stem, "Gloss_ID") or []
        if not isinstance(stem_glosses, list):
            stem_glosses = [stem_glosses]
        for stem_gloss in stem_glosses:
            data.add(
                morpho.StemGloss,
                stem["ID"],
                gloss=stem_gloss,
                stem=new_stem,
            )
        new_stem.lexeme = get_link(stem, "Lexeme_ID")

    for sslice in iter_table("stemparts"):
        new_stempart = data.add(
            morpho.StemPart,
            sslice["ID"],
            morph=data["Morph"][sslice["Morph_ID"]],
            stem=data["Stem"][sslice["Stem_ID"]],
            index=int(sslice["Index"]),
        )
        for gloss_id in sslice["Gloss_ID"]:
            data.add(
                morpho.StemPartGloss,
                sslice["ID"] + gloss_id,
                gloss=data["Gloss"][gloss_id],
                stempart=new_stempart,
            )

    for sslice in iter_table("wordformstems"):
        data.add(
            morpho.WordformStem,
            sslice["ID"],
            form=data["Wordform"][sslice["Wordform_ID"]],
            stem=data["Stem"][sslice["Stem_ID"]],
            index=[int(sslice["Index"])],
        )
    for process in iter_table("derivationalprocesses"):
        data.add(
            morpho.DerivationalProcess,
            process["ID"],
            id=process["ID"],
            name=process["Name"],
            description=process["Description"],
        )
    for derivation in iter_table("derivations"):
        sstem = get_link(derivation, "Source_ID", "Stem")
        sroot = get_link(derivation, "Root_ID", "Morph")
        new_deriv = data.add(
            morpho.Derivation,
            derivation["ID"],
            process=data["DerivationalProcess"][derivation["Process_ID"]],
            source_stem=sstem,
            source_root=sroot,
            target=data["Stem"][derivation["Target_ID"]],
        )
        for idx, stempart_id in enumerate(derivation["Stempart_IDs"]):
            data.add(
                morpho.StemPartDerivation,
                f"{derivation['ID']}-{idx}",
                stempart=data["StemPart"][stempart_id],
                derivation=new_deriv,
            )

    for cat in iter_table("inflectionalcategories"):
        data.add(morpho.InflectionalCategory, cat["ID"], id=cat["ID"], name=cat["Name"])
    for val in iter_table("inflectionalvalues"):
        data.add(
            morpho.InflectionalValue,
            val["ID"],
            id=val["ID"],
            name=val["Name"],
            category=data["InflectionalCategory"][val["Category_ID"]],
            gloss=data["Gloss"][val["Gloss_ID"]],
        )
    for infl in iter_table("inflections"):
        new_infl = data.add(
            morpho.Inflection,
            infl["ID"],
            value=data["InflectionalValue"][infl["Value_ID"]],
            stem=data["Stem"][infl["Stem_ID"]],
        )
        for wfpart in infl["Wordformpart_ID"]:
            data.add(
                morpho.WordformPartInflection,
                f"{wfpart}-{infl['ID']}",
                formpart=data["WordformPart"][wfpart],
                inflection=new_infl,
                form=get_link(infl, "Form_ID"),
            )

    for text in iter_table("texts"):
        if text["Metadata"]:
            tags = text["Metadata"].pop("tags", [])
        else:
            tags = []
        new_text = data.add(
            corpus.Text,
            text["ID"],
            id=text["ID"],
            name=text["Title"],
            description=text["Description"],
            text_metadata=text["Metadata"],
        )
        for tag in tags:
            if tag not in data["Tag"]:
                data.add(corpus.Tag, tag, id=tag, name=tag)
                data.add(
                    corpus.TextTag,
                    text["ID"] + tag,
                    tag=data["Tag"][tag],
                    text=new_text,
                )

    for spk in iter_table("speakers"):
        data.add(corpus.Speaker, spk["ID"], id=spk["ID"], name=spk["Abbreviation"])

    for ex in iter_table("ExampleTable"):
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
        if "speakers.csv" in cldf_tables:
            data.add(
                corpus.SpeakerSentence,
                ex["ID"],
                sentence=new_ex,
                speaker=data["Speaker"][ex["Speaker_ID"]],
            )
        if ex.get("Text_ID", None) is not None:
            data.add(
                corpus.TextSentence,
                ex["ID"],
                sentence=new_ex,
                text=data["Text"][ex["Text_ID"]],
                record_number=ex["Record_Number"],
                phrase_number=ex.get("Phrase_Number", None),
            )
        elif len(ex.get("Source", [])) > 0:
            bibkey, pages = Sources.parse(ex["Source"][0])
            source = data["Source"][bibkey]
            DBSession.add(
                common.SentenceReference(
                    sentence=new_ex, source=source, key=source.id, description=pages
                )
            )

    if "ExampleTable" in cldf_tables:
        demo_data.append(
            f"""As you can see in <a class="exref" example_id="{new_ex.id}"></a>, everything can be a link!\n[](ExampleTable#cldf:{new_ex.id})"""
        )

    for sf in iter_table("exampleparts"):
        data.add(
            corpus.SentencePart,
            sf["ID"],
            form=data["Wordform"][sf["Wordform_ID"]],
            sentence=data["Sentence"][sf["Example_ID"]],
            index=int(sf["Index"]),
            # form_meaning=data["FormMeaning"][
            #     sf["Form_ID"] + "-" + sf["Parameter_ID"]
            # ],
        )

    for audio in iter_table("MediaTable"):
        if audio["ID"] in data["Sentence"]:
            sentence_file = common.Sentence_files(
                object_pk=data["Sentence"][audio["ID"]].pk,
                name="%s" % audio["ID"],
                id="%s" % audio["ID"],
                mime_type="audio/wav",
            )
            DBSession.add(sentence_file)
            DBSession.flush()
            DBSession.refresh(sentence_file)
        elif audio["ID"] in data["Wordform"]:
            form_file = corpus.Wordform_files(
                object_pk=data["Wordform"][audio["ID"]].pk,
                name=audio["Name"],
                id=audio["ID"],
                mime_type="audio/wav",
            )
            DBSession.add(form_file)
            DBSession.flush()
            DBSession.refresh(form_file)

    chapters = {}
    for chapter in iter_table("chapters"):
        if chapter["ID"] == "landingpage":
            dataset.description = chapter["Description"]
        else:
            ch = data.add(
                doc.Document,
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

    for topic in iter_table("topics"):
        new_topic = data.add(
            doc.Topic,
            topic["ID"],
            id=topic["ID"],
            name=topic["Name"],
            description=topic["Description"],
        )
        for ref, label in topic["References"]:
            data.add(
                doc.TopicDocument,
                topic["ID"] + slugify(ref),
                topic=new_topic,
                document=data["Document"]["nouns"],
                label=label,
                section=ref,
            )

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
