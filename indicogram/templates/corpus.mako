<%inherit file="app.mako"/>
<% from clld_corpus_plugin.models import Text, Speaker %>
<% from clld.db.models.common import Sentence %>

<link rel="stylesheet" href="${req.static_url('clld_document_plugin:static/clld-document.css')}"/>
<%! active_menu_item = "corpus" %>


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
        <li class="active"><a href="#sentences" data-toggle="tab"> Sentences </a></li>
        <li><a href="#texts" data-toggle="tab"> Texts </a></li>
        <li><a href="#speakers" data-toggle="tab"> Speakers </a></li>
    </ul>

    <div class="tab-content" style="overflow: visible;">
        <div id="sentences" class="tab-pane active">
            ${request.get_datatable('sentences', Sentence).render()}
        </div>

        <div id="texts" class="tab-pane">
            ${request.get_datatable('texts', Text).render()}
        </div>

        <div id="speakers" class="tab-pane">
            ${request.get_datatable('speakers', Speaker).render()}
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