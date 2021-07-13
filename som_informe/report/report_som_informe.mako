## -*- coding: utf-8 -*-
<%
obj = objects[0].pool.get('wizard.create.technical.report')
report_data = obj.get_data(cursor, uid, objects[0].id)
%>
<!doctype html public "-//w3c//dtd html 4.0 transitional//en">
<html>
<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
<head>
    test
</head>
<body>
% for data_item in report_data:
    % if data_item.type == 'header':
        <%include file="/som_informe/report/components/header/header.mako" args="d=data_item" />
    % endif
    % if data_item.type == 'R101':
        <%include file="/som_informe/report/components/test/test.mako" args="d=data_item" />
    % endif
% endfor
</ul>
</body>
</html>
