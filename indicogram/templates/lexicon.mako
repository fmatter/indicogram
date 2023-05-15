<%inherit file="app.mako"/>
<% from clld_morphology_plugin.models import Lexeme, Stem, DerivationalProcess %>
<% from clld.db.models.common import Source %>

<link rel="stylesheet" href="${req.static_url('clld_document_plugin:static/clld-document.css')}"/>
<%! active_menu_item = "lexicon" %>


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
        <li class="active"><a href="#lexemes" data-toggle="tab"> Lexemes </a></li>
        <li ><a href="#stems" data-toggle="tab"> Stems </a></li>
        <li><a href="#derivation" data-toggle="tab"> Derivation </a></li>
    </ul>

    <div class="tab-content" style="overflow: visible;">

        <div id="lexemes" class="tab-pane active">
            ${request.get_datatable('lexemes', Lexeme).render()}
        </div>

        <div id="stems" class="tab-pane">
            ${request.get_datatable('stems', Stem).render()}
        </div>

        <div id="derivation" class="tab-pane">
            ${request.get_datatable('derivationalprocesss', DerivationalProcess).render()}
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