## -*- coding: utf-8 -*-
<%

obj = objects[0].pool.get('wizard.create.technical.report')

report_data = obj.get_data(cursor, uid, objects[0].id)

data = repr(report_data)
o = repr(objects)
%>
<!doctype html public "-//w3c//dtd html 4.0 transitional//en">
<html>
<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
<head>
    test
</head>
<body>
${data} <br>
${o} <br>
<b>hola</b>
<h1>test <a href="">rapid</a></h1>
<img src="https://www.somenergia.coop/wp-content/uploads/2020/12/171x107px_web_10_anys.gif">
<a href="https://www.somenergia.coop/">aixo es un link</a>
% if False:
% for data_item in report_data:
    % if i.type == 'test':
        <%include file="/som_informe/report/components/test/test.mako" args="data=data_item" />
    % endif
    % if i.type == 'test2':
        <%include file="/som_informe/report/components/test2/test2.mako" args="data=data_item" />
    % endif
% endfor
% endif
</body>
</html>
