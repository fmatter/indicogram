<%inherit file="app.mako"/>
<link rel="stylesheet" href="${req.static_url('clld_document_plugin:static/clld-document.css')}"/>

<%def name="markdown(request, content)">
    <%from clld_markdown_plugin import markdown%>
    ${markdown(request, content)|n}
</%def>

##
## define app-level blocks:
##
<%block name="header">
    ##<a href="${request.route_url('dataset')}">
    ##    <img src="${request.static_url('indicogram:static/header.gif')}"/>
    ##</a>
</%block>

${next.body()}

<%block name="footer_citation">
    ${request.dataset.formatted_name()}
    by
    <span xmlns:cc="http://creativecommons.org/ns#"
          property="cc:attributionName"
          rel="cc:attributionURL">
        ${request.dataset.formatted_editors()}
    </span>
</%block>

<script src="${req.static_url('clld_document_plugin:static/clld-document.js')}">
</script>
<script>
number_examples()
</script>