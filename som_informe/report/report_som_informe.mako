## -*- coding: utf-8 -*-
<%
obj = objects[0].pool.get('wizard.create.technical.report')
report_data = obj.get_data(cursor, uid, objects[0].id)
%>
<!doctype html public "-//w3c//dtd html 4.0 transitional//en">
<html>
<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
<head>
</head>
<body>
% for data_item in report_data:
    <%include file="/som_informe/report/components/${data_item.type}/${data_item.type}.mako" args="d=data_item" />
% endfor
</ul>
</body>
</html>
