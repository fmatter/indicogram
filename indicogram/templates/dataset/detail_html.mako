<%inherit file="../home_comp.mako"/>
<%namespace name="util" file="../util.mako"/>

<%def name="sidebar()">
    ${util.cite()}
<%include file="toc.mako"/>

</%def>

<h2>${ctx.name}</h2>

<p class="lead">
 This website is under construction.
 Feel free to look around and explore what exists so far.
</p>

<%include file="landing_page.mako"/>

