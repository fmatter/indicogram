import csv
import logging
import sys

import clld_corpus_plugin.models as corpus
import clld_document_plugin.models as doc
import clld_morphology_plugin.models as morpho
import colorlog
from clld.cliutil import Data, bibtex2source
from clld.db.meta import DBSession
from clld.db.models import common
from clld.lib import bibtex
from clldutils import licenses
import shutil
from pycldf import Sources
from tqdm import tqdm
from slugify import slugify
import shutil
from pathlib import Path

import indicogram

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


def process_cldf(data, dataset, cldf):
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
        entries = []
        if tablename[0] == tablename[0].lower():
            tablename = f"{tablename}.csv"
        if tablename in cldf_tables:
            entries = list(cldf.iter_rows(tablename))
        if entries:
            for entry in tqdm(entries, desc=tablename):
                yield entry
        # else:
        #     log.warning(f"Table '{tablename}' does not exist")

    demo_data = []

    def get_link(rec, field, datafield=None):
        if not datafield:
            datafield = field.replace("_ID", "")
        if field in rec and rec[field]:
            if isinstance(rec[field], list):
                return [data[datafield][x] for x in rec[field]]
            return data[datafield].get(rec[field])
        return None

    def add_source(entity, new_entity):
        if entity["Source"]:
            bibkey, pages = Sources.parse(entity["Source"][0])
            new_entity.source = data["Source"][bibkey]

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
        if contributor["Order"]:
            dataset.editors.append(
                common.Editor(
                    contributor=new_cont, ord=contributor["Order"], primary=True
                )
            )

    for ctb in iter_table("ContributionTable"):
        cont = data.add(
            common.Contribution,
            ctb["ID"],
            id=ctb["ID"],
            name=ctb["Name"],
            description=ctb["Description"],
        )
        for contributor in listify(ctb["Contributor"]):
            data.add(
                common.ContributionContributor,
                ctb["ID"],
                contribution=cont,
                contributor=data["Contributor"][contributor],
            )

    for rec in tqdm(bibtex.Database.from_file(cldf.bibpath), desc="Sources"):
        data.add(common.Source, rec.id, _obj=bibtex2source(rec))

    for lang in iter_table("LanguageTable"):
        data.add(
            common.Language,
            lang["ID"],
            id=lang["ID"],
            name=lang["Name"],
            latitude=lang["Latitude"],
            longitude=lang["Longitude"],
        )

    for meaning in iter_table("ParameterTable"):
        param_dict[meaning["ID"]] = meaning["Name"] or "unknown meaning"

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
            language=data["Language"][pos["Language_ID"]],
        )

    media = {}
    for med in iter_table("media"):
        if med["Download_URL"].scheme == "data":
            continue
        src_path = Path(med["Download_URL"].path)
        filename = src_path.name
        target_path = Path("audio") / filename
        if src_path.is_file() and not target_path.is_file():
            shutil.copy(src_path, target_path)
        media[med["ID"]] = filename

    for wordform in iter_table("wordforms"):
        new_form = data.add(
            morpho.Wordform,
            wordform["ID"],
            id=wordform["ID"],
            language=data["Language"][wordform["Language_ID"]],
            name=wordform["Form"],
            description=generate_description(wordform),
            parts=wordform["Morpho_Segments"],
            pos=get_link(wordform, "Part_Of_Speech", "POS"),
            contribution=get_link(wordform, "Contribution_ID")
        )
        add_source(wordform, new_form)
        if "Media_ID" in wordform and wordform["Media_ID"]:
            morpho.Wordform_files(
                object=new_form,
                id=wordform["Media_ID"],
                name=wordform["Media_ID"],
                mime_type="audio/wav",
            )

    if "wordforms.csv" in cldf_tables:
        demo_data.append(
            f"[](FormTable#cldf:{new_form.id}) is one of my favorite [](LanguageTable#cldf:{new_form.language.id}) wordforms."
        )

    for morpheme in iter_table("morphemes"):
        new_morpheme = data.add(
            morpho.Morpheme,
            morpheme["ID"],
            id=morpheme["ID"],
            name=morpheme["Name"],
            language=data["Language"][morpheme["Language_ID"]],
            description=generate_description(morpheme),
            contribution=get_link(morpheme, "Contribution_ID")
        )
        add_source(morpheme, new_morpheme)

    for morph in iter_table("morphs"):
        new_morph = data.add(
            morpho.Morph,
            morph["ID"],
            id=morph["ID"],
            language=data["Language"][morph["Language_ID"]],
            name=morph["Name"],
            description=generate_description(morph),
            contribution=get_link(morph, "Contribution_ID"),
            pos=get_link(morph, "Part_Of_Speech", "POS"),
        )
        add_source(morph, new_morph)
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
        new_form = data.add(
            morpho.Form,
            form["ID"],
            id=form["ID"],
            name=form["Form"],
            parts=form.get("Morpho_Segments"),
            description=generate_description(form),
            language=data["Language"][form["Language_ID"]],
            contribution=get_link(form, "Contribution_ID")
        )
        add_source(form, new_form)

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
            pos=get_link(lexeme, "Part_Of_Speech", "POS"),
            contribution=get_link(lexeme, "Contribution_ID")
        )
        if "Paradigm_View" in lexeme and lexeme["Paradigm_View"]:
            new_lexeme.paradigm_x = lexeme["Paradigm_View"]["x"]
            new_lexeme.paradigm_y = lexeme["Paradigm_View"]["y"]

    for stem in iter_table("stems"):
        new_stem = data.add(
            morpho.Stem,
            stem["ID"],
            id=stem["ID"],
            name=stem["Name"],
            description=generate_description(stem),
            language=data["Language"][stem["Language_ID"]],
            parts=stem["Morpho_Segments"],
            contribution=get_link(stem, "Contribution_ID")
        )
        add_source(stem, new_stem)
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
            index=sslice["Index"],
        )
    for process in iter_table("derivationalprocesses"):
        data.add(
            morpho.DerivationalProcess,
            process["ID"],
            id=process["ID"],
            name=process["Name"],
            description=process["Description"],
            language=get_link(process, "Language_ID"),
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
        data.add(
            morpho.InflectionalCategory,
            cat["ID"],
            id=cat["ID"],
            name=cat["Name"],
            description=cat["Description"],
            value_order=cat.get("Value_Order", []),
        )
    for val in iter_table("inflectionalvalues"):
        data.add(
            morpho.InflectionalValue,
            val["ID"],
            id=val["ID"],
            name=val["Name"],
            category=data["InflectionalCategory"][val["Category_ID"]],
            gloss=get_link(val, "Gloss_ID"),
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
            name=text["Name"],
            description=text["Description"],
            text_metadata=text["Metadata"],
        )
        add_source(text, new_text)
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
        data.add(corpus.Speaker, spk["ID"], id=spk["ID"], name=spk["Name"])

    for ex in iter_table("ExampleTable"):
        ex["Analyzed_Word"] = ["" if x is None else x for x in ex["Analyzed_Word"]]
        ex["Gloss"] = ["" if x is None else x for x in ex["Gloss"]]
        new_ex = data.add(
            corpus.Record,
            ex["ID"],
            id=ex["ID"],
            name=ex["Primary_Text"],
            description=ex["Translated_Text"],
            analyzed="\t".join(ex["Analyzed_Word"]),
            gloss="\t".join(ex["Gloss"]),
            language=data["Language"][ex["Language_ID"]],
            comment=ex["Comment"],
            contribution=get_link(ex, "Contribution_ID")
        )
        if "Original_Translation" in ex:
            new_ex.markup_description = ex["Original_Translation"]
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
        if "Media_ID" in ex and ex["Media_ID"]:
            common.Sentence_files(
                object=new_ex,
                id=ex["Media_ID"],
                name=ex["Media_ID"],
                mime_type="audio/wav",
            )
        elif ex["ID"] in media:
            common.Sentence_files(
                object=new_ex,
                id=ex["ID"],
                name=ex["ID"],
                mime_type="audio/wav",
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
            sentence=data["Record"][sf["Example_ID"]],
            index=int(sf["Index"]),
            # form_meaning=data["FormMeaning"][
            #     sf["Form_ID"] + "-" + sf["Parameter_ID"]
            # ],
        )

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
        for ref in topic["References"]:
            data.add(
                doc.TopicDocument,
                topic["ID"] + slugify(ref["ID"]),
                topic=new_topic,
                document=data["Document"][ref["Chapter"]],
                label=ref["Label"],
                section=ref["ID"],
            )
    for abbr in iter_table("abbreviations"):
        data.add(
            common.GlossAbbreviation,
            abbr["ID"],
            id=abbr["ID"],
            name=abbr["Description"],
        )

    for table in cldf_tables:
        if table == "topics.csv":
            continue
        for row in cldf.iter_rows(table):
            if "References" in row and row["References"]:
                refs = [
                    f'<a href="/documents/{ref["Chapter"]}#{ref["ID"]}">{ref["Label"]}</a>'
                    for ref in row["References"]
                ]
                data[table.replace("s.csv", "").capitalize()][
                    row["ID"]
                ].markup_description = (
                    "Discussed in:<br><ul>"
                    + "\n".join([f"<li>{x}</li>" for x in refs])
                    + "</ul>"
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


def main(args):
    cldf = args.cldf  # passed in via --cldf
    data = Data()
    if "http" in cldf.properties.get("dc:identifier", ""):
        domain = cldf.properties.get("dc:identifier").split("://")[1]
    else:
        domain = "example.org/"
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
    process_cldf(data, dataset, cldf)


def prime_cache(args):
    """If data needs to be denormalized for lookup, do that here.
    This procedure should be separate from the db initialization, because
    it will have to be run periodically whenever data has been updated.
    """
