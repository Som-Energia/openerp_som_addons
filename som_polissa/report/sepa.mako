## -*- encoding: utf-8 -*-
<%namespace file="som_polissa/report/sepa_ca.mako" import="sepa_ca"/>
<%namespace file="som_polissa/report/sepa_es.mako" import="sepa_es"/>
<!doctype html public "-//w3c//dtd html 4.0 transitional//en">
<html>
<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
<head>
    <link rel="stylesheet" href="${addons_path}/som_polissa/report/sepa.css"/>
</head>
<body>
%for data in objects:
    %if data['lang'] == 'ca_ES':
        ${sepa_ca(data, not loop.last)}
    %else:
        ${sepa_es(data, not loop.last)}
    %endif
%endfor
</body>
</html>
