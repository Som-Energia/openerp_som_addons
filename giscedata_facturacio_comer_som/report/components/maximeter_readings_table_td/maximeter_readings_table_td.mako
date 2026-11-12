<%page args="readings_m" />
<style>
<%include file="maximeter_readings_table_td.css" />
</style>
<% import locale %>
% if readings_m.is_visible:
    <div class="lectures_max${len(readings_m.periodes_r)>=3 and '30' or ''}">
        <h1>${_(u"MAXÍMETRE")}</h1>
        <table style="margin: 1em">
            <tr>
                <th>&nbsp;</th>
                % for periode in readings_m.periodes_m:
                    <th style="text-align: center;">${periode}</th>
                % endfor
            </tr>
            <tr>
                <th>Potència contractada</th>
                % for iteracio, periode in enumerate(readings_m.periodes_m):
                    <td style="text-align: center;">${locale.str(locale.atof(formatLang(readings_m.lectures_m[iteracio][1], digits=3)))}</td>
                % endfor
            </tr>
            <tr>
                <th>Lectura maxímetre</th>
                % for iteracio, periode in enumerate(readings_m.periodes_m):
                    <td style="text-align: center;">${locale.str(locale.atof(formatLang(readings_m.lectures_m[iteracio][2], digits=3)))}</td>
                % endfor
            </tr>
            <tr>
                <th>Potència facturada</th>
                % for iteracio, periode in enumerate(readings_m.periodes_m):
                    <td style="text-align: center;">${locale.str(locale.atof(formatLang(readings_m.fact_potencia[sorted(readings_m.fact_potencia)[iteracio]], digits=3)))}</td>
                % endfor
            </tr>
            % if readings_m.has_exces_potencia:
                <tr>
                    <th>Quantitat excedida</th>
                    % for iteracio, periode in enumerate(readings_m.periodes_m):
                        <td style="text-align: center;">${int(readings_m.exces_m[iteracio][0])}</td>
                    % endfor
                </tr>
                <tr>
                    <th>Import excés de Potència (en Euros)</th>
                    % for iteracio, periode in enumerate(readings_m.periodes_m):
                        <td style="text-align: center;">${formatLang(readings_m.exces_m[iteracio][1])}</td>
                    % endfor
                </tr>
            % endif
        </table>
    </div>
% endif
