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
        ${_(u"L'any 2020, Som Energia ha contribuït amb 397.408,41 euros al finançament del bo social. Totes les comercialitzadores estan obligades a finançar el bo social, que només poden oferir les comercialitzadores de referència")}
        %if id_comments.language == 'ca_ES':
            <a href="https://ca.support.somenergia.coop/article/171-que-es-el-bo-social">${_(u"(més informació).")}</a>
        %else:
            <a href="https://es.support.somenergia.coop/article/208-que-es-el-bono-social">${_(u"(més informació).")}</a>
        %endif
    </p>