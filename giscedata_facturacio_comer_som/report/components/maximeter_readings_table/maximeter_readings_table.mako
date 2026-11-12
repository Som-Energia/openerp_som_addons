<%page args="readings_m" />
<style>
<%include file="maximeter_readings_table.css" />
</style>
<% import locale %>
% if readings_m.is_visible:
    <div class="lectures_max${len(readings_m.periodes_r)>=3 and '30' or ''} ${readings_m.visible_side_by_side}">
        <h1>${_(u"MAXÍMETRE")}</h1>
        <table style="margin: 1em">
            <tr>
                <th>&nbsp;</th>
                <th style="text-align: center;">Potència contractada</th>
                <th style="text-align: center;">Lectura maxímetre</th>
                <th style="text-align: center;">Potència facturada</th>
                % if readings_m.has_exces_potencia:
                    <th style="text-align: center;">Quantitat excedida</th>
                    <th style="text-align: center;">Import excés de Potència <br/> (en Euros)</th>
                % endif
            </tr>
            % for iteracio, periode in enumerate(readings_m.periodes_m):
                <tr>
                    <th style="text-align: center;">${periode}</th>
                    <td style="text-align: center;">${locale.str(locale.atof(formatLang(readings_m.lectures_m[iteracio][1], digits=3)))}</td>
                    <td style="text-align: center;">${locale.str(locale.atof(formatLang(readings_m.lectures_m[iteracio][2], digits=3)))}</td>
                    <td style="text-align: center;">${locale.str(locale.atof(formatLang(readings_m.fact_potencia[sorted(readings_m.fact_potencia)[iteracio]], digits=3)))}</td>
                    % if readings_m.has_exces_potencia:
                        <td style="text-align: center;">${int(readings_m.exces_m[iteracio][0])}</td>
                        <td style="text-align: center;">${formatLang(readings_m.exces_m[iteracio][1])}</td>
                    % endif
                </tr>
            % endfor
        </table>
    </div>
% endif
