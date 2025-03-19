<%page args="hc" />
% if hc.is_visible:
<style>
<%include file="hourly_curve.css" />
</style>
<%
import csv
from giscedata_facturacio_indexada.report.report_indexada_helpers import getCsvData, colorPicker, getAxisAndData
from collections import namedtuple
import json

green_deg = ['#ddffdd', '#aaffaa', '#77ff77', '#33ff33', '#00ff00']
Mode = namedtuple('Mode', ['title', 'colors', 'factor'])
modes = {
    'graph': Mode(
            title=_(u'Evolució horaria'),
            colors=['#0000aa', '#ff0000',],
            factor=1,
    ),
    'curvegraph': Mode(
            title=_(u'Consum'),
            colors=['#00aa00', '#ff0000',],
            factor=1,
    ),
    'phf': Mode(
            title=_(u'Preu Horari Final (cts. de €)'),
            colors=['#00aa00', '#88aa88', '#ffffff', '#ffff00', '#ff8f00'],
            factor=100,
        ),
    'curve': Mode(
            title=_(u'Consum Horari (kWh)'),
            colors=green_deg,
            factor=1,
        ),
    'pmd': Mode(
            title=_(u'Preu OMIE €/kWh'),
            colors=green_deg,
            factor=1,
        ),
    'pc3_ree': Mode(
            title=_(u'Pagament per capacitat mig (€/kWh'),
            colors=green_deg,
            factor=1,
        ),
    'perdues': Mode(
            title=_(u'Pèrdues (%)'),
            colors=green_deg,
            factor=1,
        ),
}
%>
<%def name="graph(nom, mode1, mode2, curve_data=None)">
    <%
        GraphModeObj = modes[nom]
        data = []
        colors = ['#abb439', '#c58700']
        titles = []
        index = 0
        for mode_str in [mode1, mode2]:
            mode
            data.append([])
            ModeObj = modes[mode_str]
            if curve_data is None:
                data_csv = getCsvData(objects[0], user, mode_str)
                csv_stream = data_csv
            else:
                from StringIO import StringIO
                csv_stream = StringIO(curve_data)

            csv_lines = csv.reader(csv_stream, delimiter=';')
            rows = []
            for row in csv_lines:
                rows.append((row[0], float(row[1])))
            collection = dict(rows)
            if index == 0 and nom=='curvegraph':
                axis, data[index] = getAxisAndData(collection, 'dayly')
            else:
                axis, data[index] = getAxisAndData(collection)
            colors.append(GraphModeObj.colors[index])
            titles.append(ModeObj.title)
            index += 1
        styles = ['area-step', 'spline']
        titles = [_('Consums totals per dies (kWh)'), _('Corba horària de potència (kW)')]
    %>
    <div id="${nom}"></div>
    <script>
    var axis = [${axis}]; // [["2018-01-01 01", "2018-01-01 02",...]]
    var data = [
        ${data[0]},
        ${data[1]},
    ];
    var titles = ${json.dumps(titles)};
    var colors = ${colors};
    var styles = ${styles};
    try {
    var chart = c3.generate({
        bindto: '#${nom}',
        size: {
            height: 200,
            width: 700,
        },
        data: {
            x: 'x',
            columns: [
                ['x'].concat(axis[0]),
                ['data1'].concat(data[0]),
                ['data2'].concat(data[1]),
            ],
            axes: {
                data2: 'y2',
            },
            types: {
                data1: styles[0],
                data2: styles[1],
            },
            xFormat: '%Y-%m-%d %H',
            names: {
                data1: titles[0],
                data2: titles[1],
            },
            colors: {
               data1: colors[0],
               data2: colors[1],
            }
        },
        point: {
            show: false
        },
        axis: {
          x: {
             type: 'timeseries',
             tick: {
                     count: axis[0].length / 24,
                     format: '%d/%m',
             }
          },
          y2: {
            show: true}
        }
    });
    }
    catch(err) {
        document.writeln(err.message);
    }
    </script>
</%def>
    <div class="pl_15">
        <h1 class="${hc.has_agreement_partner and 'agreement' or ''}partner">${_(u"Ús elèctric i corba horària")}</h1>
        <% curve = hc.factura_data %>
        %if curve:
            <%
            mode = "curvegraph"
            graph(mode, 'curve', 'curve', curve_data=curve)
            %>
        %endif
        <div style="clear: both;"></div>

    <p class="profile_curve_text">
    % if hc.profiled_curve:
        ${_(u"Corbes horàries perfilades segons l'ús mensual informat per la distribuïdora.")}
    % else:
        ${_(u"Corbes horàries informades per la distribuïdora.")}
    % endif
    </p>
    </div>
% endif
