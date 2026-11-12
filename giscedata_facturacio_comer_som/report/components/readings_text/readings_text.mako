<%page args="readings" />
<style>
<%include file="readings_text.css" />
</style>
% if readings.is_visible:
    <div class="lectures_text${len(readings.periodes_a)>=3 and '30' or ''}">
    % if readings.has_autoconsum:
        <p>${_("* Aquest consum té l'ajust corresponent al balanç horari ")}
            %if readings.lang == 'ca_ES':
                <a href="https://ca.support.somenergia.coop/article/849-autoproduccio-que-es-el-balanc-net-horari">${_(u"(más información).")}</a>
            %else:
                <a href="https://es.support.somenergia.coop/article/850-autoproduccion-que-es-el-balance-neto-horario">${_(u"(més informació).")}</a>
            %endif
        </p>
    % else:
        <p>${_("* Aquesta factura recull un ajust de consum de períodes anteriors per part de la distribuïdora.")}</p>
    % endif
    </div>
% endif
