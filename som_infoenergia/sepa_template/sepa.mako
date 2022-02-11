## -*- encoding: utf-8 -*-
<%
report = objects[0]
data = report.sepa_particulars_data()
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
