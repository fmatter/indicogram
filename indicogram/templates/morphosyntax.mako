<%inherit file="app.mako"/>
<% from clld_morphology_plugin.models import Wordform, Morph, Morpheme, InflectionalCategory, POS %>
<% from clld_corpus_plugin.models import Speaker %>

<link rel="stylesheet" href="${req.static_url('clld_document_plugin:static/clld-document.css')}"/>
<%! active_menu_item = "morphosyntax" %>


## <%def name="markdown(request, content)">
##     <%from clld_markdown_plugin import markdown%>
##     ${markdown(request, content)|n}
## </%def>

##
## define app-level blocks:
##
<%block name="header">
    ## <a href="${request.route_url('dataset')}">
    ##    <img src="${request.static_url('indicogram:static/header.gif')}"/>
    ## </a>
</%block>

<div class="tabbable">

    <ul class="nav nav-tabs">
        <li class="active"><a href="#wordforms" data-toggle="tab"> Wordforms </a></li>
        <li><a href="#morphs" data-toggle="tab"> Morphs </a></li>
        <li><a href="#morphemes" data-toggle="tab"> Morphemes </a></li>
        <li><a href="#pos" data-toggle="tab"> Parts of speech </a></li>
        <li><a href="#inflection" data-toggle="tab"> Inflection </a></li>
    </ul>

    <div class="tab-content active" style="overflow: visible;">

        <div id="wordforms" class="tab-pane active">
            ${request.get_datatable('wordforms', Wordform).render()}
        </div>

        <div id="morphs" class="tab-pane">
            ${request.get_datatable('morphs', Morph).render()}
        </div>

        <div id="morphemes" class="tab-pane">
            ${request.get_datatable('morphemes', Morpheme).render()}
        </div>

        <div id="pos" class="tab-pane">
            ${request.get_datatable('poss', POS).render()}
        </div>

        <div id="inflection" class="tab-pane">
            ${request.get_datatable('inflectionalcategorys', InflectionalCategory).render()}
        </div>

    </div>

</div>
## ${next.body()}

<%block name="footer_citation">
    ${request.dataset.formatted_name()}
    by
    <span xmlns:cc="http://creativecommons.org/ns#"
          property="cc:attributionName"
          rel="cc:attributionURL">
        ${request.dataset.formatted_editors()}
    </span>
</%block>