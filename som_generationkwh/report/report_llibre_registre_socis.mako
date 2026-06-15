## -*- coding: utf-8 -*-
<%
import ast
pool = objects[0].pool
cursor = objects[0]._cr
uid = user.id
dades = data.get('dades', [])
header = data.get('header', {})
soci_anterior = ''
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
<div class="break-after">
    <br />
    <br />
    <h1>SOM ENERGIA SCCL</h1>
    <br />
    <h2>LIBR0 DE SOCIOS Y APORTACIONES SOCIALES</h2>
    <br />
    <h3>Tomo 1</h3>
    <br />
    <br />
    <p>Fecha de apertura: ${header['date_from']}</p>
    <p>Fecha de cierre: ${header['date_to']}</p>
    <br />
    <br />
    <p>Ejercicio económico ${header['date_to'][:4]}</p>
</div>

<h3>LIBRO DE REGISTRO DE SOCIOS</h3>
<table style="width:100%">
     <tr>
        <th><b>Número de socio/socia</b></th>
        <th><b>Apellidos, Nombre</b></th>
        <th><b>DNI/NIE</b></th>
        <th><b>Tipo de socio/a</b></th>
        <th><b>Fecha de incorporación</b></th>
        <th><b>Fecha de baja</b></th>
        <th><b>Modificación</b></th>
        <th><b>Tipo de aportación</b></th>
        <th><b>Fecha desembolso / reembolso</b></th>
        <th><b>Importe</b></th>
        <th><b>Email</b></th>
        <th><b>Dirección</b></th>
      </tr>
%for dades_soci in dades:
    <%
        mostrar_dades = True
    %>
%    for dades_apo in dades_soci['inversions']:
      <tr class="keep-together">
%      if mostrar_dades:
        <td>${dades_soci['num_soci']}</td>
        <td>${dades_soci['nom']}</td>
        <td>${dades_soci['dni']}</td>
        <td>Consumidor</td>
        <td>${dades_soci['data_alta']}</td>
        <td>${dades_soci['data_baixa']}</td>
%      else:
        <td></td>
        <td></td>
        <td></td>
        <td></td>
        <td></td>
        <td></td>
%      endif
        <td></td>
%      if dades_apo['concepte'] == u'Obligatoria':
        <td>(1) ${dades_apo['concepte']}</td>
%      else:
        <td>(2) ${dades_apo['concepte']}</td>
%      endif
        <td>${dades_apo['data']}</td>
        <td>${dades_apo['import']}€</td>
%      if mostrar_dades:
        <td>${dades_soci['email']}</td>
        <td>${dades_soci['adreca']} ${dades_soci['cp']} ${dades_soci['municipi']}</td>
%      else:
        <td></td>
        <td></td>
%      endif
      </tr>
      <tr>
    <%
        mostrar_dades = False
    %>
%endfor
%endfor
  </table>
  <br/>
  <div>(1) derecho de reembolso rehusable por el Consejo Rector</div>
  <div>(2) derecho de reembolso rehusable por el Consejo Rector siempre que el importe total de los reembolsos de las aportaciones voluntarias haya superado antes de la petición de reembolso el 10% del capital social anual según el art. 14 de los Estatutos</div>
  <br />
  <br />
</body>
</html>
