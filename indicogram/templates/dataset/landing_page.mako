<%from clld_markdown_plugin import markdown%> ${markdown(request, ctx.description)|n}

<script src="${req.static_url('clld_document_plugin:static/clld-document.js')}">
</script>
<script>
numberExamples()
</script>