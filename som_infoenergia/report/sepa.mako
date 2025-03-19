## -*- encoding: utf-8 -*-
<%
import locale
locale.setlocale(locale.LC_NUMERIC,'es_ES.utf-8')
r_obj = objects[0].pool.get('sepa.report')
dades = r_obj.get_report_data(cursor, uid, objects)
%>
<!doctype html public "-//w3c//dtd html 4.0 transitional//en">
<html>
<head>
    <meta http-equiv="content-type" content="text/html; charset=utf-8"/>
    <link rel="stylesheet" href="${addons_path}/som_infoenergia/report/sepa.css"/>
</head>
<body>
% for dada in dades:
    <%include file="/som_infoenergia/report/components/main/main.mako" args="d=dada.main" />
% endfor
</body>
</html>
