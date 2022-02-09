## -*- coding: utf-8 -*-
<%
import locale
locale.setlocale(locale.LC_NUMERIC,'es_ES.utf-8')
r_obj = objects[0].pool.get('report.indexed.offer')
data = r_obj.get_report_data(cursor, uid, objects[0])
%>
<!doctype html>
<html>
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
</head>
<body>
  <%include file="/som_infoenergia/report/components/first_page/first_page.mako" args="d=data.first_page" />
<p style="page-break-after:always"></p>
  <%include file="/som_infoenergia/report/components/header/header.mako" args="d=data.header" />
  <%include file="/som_infoenergia/report/components/antecedents/antecedents.mako" args="d=data.antecedents" />
</body>
</html>
