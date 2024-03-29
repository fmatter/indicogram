<%inherit file="app.mako"/>
<% from clld_document_plugin.models import Document, Topic %>
<% from clld.db.models.common import Source %>

<link rel="stylesheet" href="${req.static_url('clld_document_plugin:static/clld-document.css')}"/>
<%! active_menu_item = "description" %>


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
        <li class="active"><a href="#chapters" data-toggle="tab"> Chapters </a></li>
        <li><a href="#topics" data-toggle="tab"> Topics </a></li>
        <li><a href="#sources" data-toggle="tab"> Sources </a></li>
    </ul>

    <div class="tab-content" style="overflow: visible;">
        <div id="chapters" class="tab-pane active">
            ${request.get_datatable('documents', Document).render()}
        </div>

        <div id="topics" class="tab-pane">
            ${request.get_datatable('topics', Topic).render()}
        </div>

        <div id="sources" class="tab-pane">
            ${request.get_datatable('sources', Source).render()}
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