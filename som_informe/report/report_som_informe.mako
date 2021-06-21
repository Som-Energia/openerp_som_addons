## -*- coding: utf-8 -*-
<%
import locale
locale.setlocale(locale.LC_NUMERIC,'es_ES.utf-8')

r_obj = objects[0].pool.get('giscedata.facturacio.factura.report')
report_data = r_obj.get_report_data(cursor, uid, objects)

%>
<!doctype html public "-//w3c//dtd html 4.0 transitional//en">
<html>
<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
<head>
    test
</head>
<body>
% for data_item in report_data:
    % if i.type == 'test':
        <%include file="/som_informe/report/components/test/test.mako" args="data=data_item" />
    % endif
    % if i.type == 'test2':
        <%include file="/som_informe/report/components/test2/test2.mako" args="data=data_item" />
    % endif
% endfor
</body>
</html>
