<%page args="id_comments" />
<style>
<%include file="invoice_details_comments.css" />
</style>
    <p style="font-size: .8em"><br />
        %if id_comments.invoice_comment:
            <div>${id_comments.invoice_comment}</div>
        %endif
        ${_(u"Si vols conèixer el detall de les teves dades horàries d’ús d’electricitat i de potència i disposes d’un comptador amb la telegestió activada, t’animem a registrar-te i accedir gratuïtament al portal web de la teva empresa distribuïdora: ")}
        %if id_comments.has_web:
            <a href="${id_comments.web_distri}">${id_comments.web_distri}</a>
        %else:
            <i>${_(u"(Ho sentim, %s encara no ens ha facilitat l’enllaç al portal)") % id_comments.distri_name }</i>
        %endif
        <br/>
        ${_(u"Els preus dels termes de peatge d'accés són els publicats a ORDRE IET/107/2014.")}<br />
        ${_(u"Els preus del lloguer dels comptadors són els establerts a ORDRE ITC/3860/2007.")}<br />
    </p>
