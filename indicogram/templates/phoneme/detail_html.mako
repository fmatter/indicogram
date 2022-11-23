<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "phonemes" %>

<ul>
% for part in ctx.forms:
    %if part.form.audio:
        <li>
            <audio id='${part.form.name}_player' controls="controls"><source src="/audio/${part.form.audio}" type="audio/x-wav"></source></audio> <img class='playbutton' onclick='${part.form.name}_player.play()' src='/static/play.png'>

            ${h.link(request, part.form)}
        </li>
    % endif
% endfor
% for part in ctx.forms:
    %if not part.form.audio:
        <li>${h.link(request, part.form)}</li>
    % endif
% endfor
</ul>

</article>

