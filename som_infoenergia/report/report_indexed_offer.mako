## -*- coding: utf-8 -*-
<%
import locale
locale.setlocale(locale.LC_NUMERIC,'es_ES.utf-8')
r_obj = objects[0].pool.get('report.indexed.offer')
datas = r_obj.get_report_data(cursor, uid, objects)
%>
<!doctype html>
<html>
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
<link rel="stylesheet" href="${addons_path}/som_infoenergia/report/report_indexed_offer.css">
</head>
<body>
% for data in datas:
  <%include file="/som_infoenergia/report/components/first_page/first_page.mako" args="d=data.first_page" />
<p style="page-break-after:always"></p>
  <%include file="/som_infoenergia/report/components/header/header.mako" args="d=data.header" />
  <%include file="/som_infoenergia/report/components/antecedents/antecedents.mako" args="d=data.antecedents" />
  <%include file="/som_infoenergia/report/components/objecte/objecte.mako" args="d=data.objecte" />
  <%include file="/som_infoenergia/report/components/cond_contr/cond_contr.mako" args="d=data.cond_contr" />
<p style="page-break-after:always"></p>
  <%include file="/som_infoenergia/report/components/power_prices/power_prices.mako" args="d=data.power_prices" />
  <%include file="/som_infoenergia/report/components/energy_prices/energy_prices.mako" args="d=data.energy_prices" />
  <%include file="/som_infoenergia/report/components/tail_text/tail_text.mako" args="d=data.tail_text" />
  <%include file="/som_infoenergia/report/components/conclusions/conclusions.mako" args="d=data.conclusions" />
% if len(datas) > 0 and id(data) != id(datas[-1]):
  <p style="page-break-after:always"></p>
% endif
% endfor
</body>
</html>
