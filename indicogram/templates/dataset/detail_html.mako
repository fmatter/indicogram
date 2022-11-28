<%inherit file="../home_comp.mako"/>
<%namespace name="util" file="../util.mako"/>

<%def name="sidebar()">
    ${util.cite()}
<%include file="toc.mako"/>

</%def>

<h2>${ctx.name}</h2>

<p class="lead">
    Welcome to your digital grammar template.
    Change this text in templates/dataset/detail_html.mako
</p>

<%include file="landing_page.mako"/>

