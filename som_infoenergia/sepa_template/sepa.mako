## -*- encoding: utf-8 -*-
<%
r_obj = objects[0].pool.get('payment.mandate')
datas = report.get_report_data(cursor, uid, objects)
%>

<!doctype html public "-//w3c//dtd html 4.0 transitional//en">
<html>
<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
<head>
    <link rel="stylesheet" href="${addons_path}/som_infoenergia/sepa_template/sepa.css"/>
</head>
<body>
    <%include file="/som_infoenergia/sepa_template/components/main/main.mako" args="d=data.main" />
</body>
</html>
