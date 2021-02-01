## -*- coding: utf-8 -*-
<%
import ast
pool = objects[0].pool
cursor = objects[0]._cr
uid = user.id
dades = data.get('dades', [])
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

</style>
</head>
<body>
%for dades_soci in dades.values():
<h3>LIBRO DE REGISTRO DE SOCIOS</h3>
<table style="width:100%">
     <tr>
        <td><b>Tipo de socio/a:</b></td>
        <td>${dades_soci['tipus']}</td>
        <td><b>Número de socio/socia:</b></td>
        <td>${dades_soci['num_soci']}</td>
      </tr>
      <tr>
        <td><b>Apellidos, Nombre:</b></td>
        <td>${dades_soci['nom']}</td>
        <td><b>DNI/NIE:</b></td>
        <td>${dades_soci['dni']}</td>
      </tr>
      <tr>
        <td><b>Email:</b></td>
        <td colspan="3">${dades_soci['email']}</td>
      </tr>
      <tr>
        <td><b>Dirección:</b></td>
        <td>${dades_soci['adreca']}</td>
        <td><b>Municipio:</b></td>
        <td>${dades_soci['municipi']}</td>
      </tr>
      <tr>
        <td><b>Código Postal:</b></td>
        <td>${dades_soci['cp']}</td>
        <td><b>Provincia:</b></td>
        <td>${dades_soci['provincia']}</td>
      </tr>
      <tr>
        <td><b>Fecha de incorporación:</b></td>
        <td>${dades_soci['data_alta']}</td>
        <td><b>Fecha de baja:</b></td>
        <td>${dades_soci['data_baixa']}</td>
      </tr>
      <tr>
        <td colspan="3"><b>Capital social obligatorio suscrito en la incorporación:</b></td>
        <td>100€</td>
      </tr>
      <tr>
        <td colspan="3"><b>Capital social voluntario suscrito en la incorporación:</b></td>
        <td>0€</td>
      </tr>
   </table>
<br/>
<h3>EVOLUCIÓN DE LAS APORTACIONES</h3>
<table class="apo_table" style="width=100%">
    <tr>
       <th rowspan="2" style="width=10%">Fecha</th>
       <th rowspan="2" style="width=30%">Concepto</th>
       <th colspan="2">Aportación obligatoria</th>
       <th colspan="2">Aportación volutaria</th>
       <th rowspan="2">TOTAL</th>
     </tr>
     <tr>
        <th>Derecho de reembolso</th>
        <th>Derecho de reembolso rehusable por el Consejo Rector</th>
        <th>Derecho de reembolso</th>
        <th>Derecho de reembolso rehusable por el Consejo Rector *</th>
     </tr>
%    for dades_apo in dades_soci['inversions']:
      <tr>
       <td>${dades_apo['data_compra']}</td>
       <td>${dades_apo['concepte']}</td>
       <td></td>
%      if dades_apo['concepte'] == u'Aportación obligatoria':
       <td>${dades_apo['import']}€</td>
%      else:
       <td></td>
%      endif
       <td></td>
%      if dades_apo['concepte'] == u'Aportación voluntaria':
       <td>${dades_apo['import']}€</td>
%      else:
      <td></td>
%      endif
       <td>${dades_apo['total']}€</td>
     </tr>
     %    endfor
  </table>
  <div>*rehusable siempre que el importe total de los reembolsos de las aportaciones voluntarias haya superado antes de la petición de reembolso el 10% del capital social anual según el art. 14 de los Estatutos</div>
  <br />
  <br />
%endfor
</body>
</html>
