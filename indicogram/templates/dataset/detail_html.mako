<%inherit file="../home_comp.mako"/>
<%namespace name="util" file="../util.mako"/>

<%def name="sidebar()">
    ${util.cite()}
<%include file="toc.mako"/>

</%def>

<h2>${ctx.name}</h2>

<p class="lead">
% if "abstract" in ctx.jsondata:
${ctx.jsondata["abstract"]}
% else:
 This website is under construction.
 Feel free to look around and explore what exists so far.
% endif
</p>

<%include file="landing_page.mako"/>

