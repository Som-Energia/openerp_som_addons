## -*- coding: utf-8 -*-
<%
import ast
pool = objects[0].pool
cursor = objects[0]._cr
uid = user.id
summary_dades = data.get('dades', [])
header = data.get('header', {})
%>
<!doctype html public "-//w3c//dtd html 4.0 transitional//en">
<html>
<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
<head>
<style>
html {
  margin: 24px;
}
.apo_table {
  border-collapse: collapse;
  margin-bottom: 8px;
}
.apo_table, .apo_table th, .apo_table td {
  border: 1px solid black;
}
.apo_table td, .apo_table th {
 padding: 8px;
}
.apo_table td {
  white-space: nowrap;
}

<!-- Print pages management -->
.keep-together {
    page-break-inside: avoid;
}

.break-before {
    page-break-before: always;
}

.break-after {
    page-break-after: always;
}
</style>
</head>
<body>
% if len(summary_dades) > 0:
        <div class="break-after">
        <br />
        <br />
        <h1>SOM ENERGIA SCCL</h1>
        <br />
        <h2>RESUMEN DEL LIBR0 DE SOCIOS Y APORTACIONES SOCIALES</h2>
        <br />
        <br />
        <p>Fecha de apertura: ${header['date_from']}</p>
        <p>Fecha de cierre: ${header['date_to']}</p>
        <br />
        <br />
        <p>Ejercicio económico ${header['date_to'][:4]}</p>
        </div>

        <div>
                <p><b>Número de altas : </b>${summary_dades['numero_altes']}</p>
                <p><b>Número de bajas : </b>${summary_dades['numero_baixes']}</p>
                <p><b>Total de aportaciones de capital voluntarias : </b>${_(u"%s €") % (formatLang(summary_dades['total_import_voluntari'], digits=2))}</p>
                <p><b>Total de capital voluntario retirado : </b>${formatLang(summary_dades['total_import_voluntari_retirat'], digits=2)}€</p>
        </div>
% endif
</body>
</html>
