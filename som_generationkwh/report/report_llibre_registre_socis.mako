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
</head>                                                                                       
<body>                                                                                        
Hola!

%for dades_soci in dades.values():
<div>LIBRO DE REGISTRO DE SOCIOS</div>
<table style="width:100%">
     <tr>
        <td>Tipo de socio/a:</td>
        <td>${dades_soci['tipus']}</td>
        <td>Número de socio/socia:</td>
        <td>${dades_soci['num_soci']}</td>
      </tr>
      <tr>
        <td>Apellidos, Nombre:</td>
        <td>${dades_soci['nom']}</td>
        <td>DNI/NIE:</td>
        <td>${dades_soci['dni']}</td>
      </tr>
      <tr>
        <td>Email:</td>
        <td colspan="3">${dades_soci['email']}</td>
      </tr>
      <tr>
        <td>Dirección:</td>
        <td>${dades_soci['adreca']}</td>
        <td>Municipio:</td>
        <td>${dades_soci['municipi']}</td>
      </tr>
      <tr>
        <td>Código Postal:</td>
        <td>${dades_soci['cp']}</td>
        <td>Provincia:</td>
        <td>${dades_soci['provincia']}</td>
      </tr>
      <tr>
        <td>Fecha de incorporación:</td>
        <td>${dades_soci['data_alta']}</td>
        <td>Fecha de baja:</td>
        <td>${dades_soci['data_baixa']}</td>
      </tr>
      <tr>
        <td colspan="3">Capital social obligatorio suscrito en la incorporación:</td>
        <td>100€</td>
      </tr>
      <tr>
        <td colspan="3">Capital social voluntario suscrito en la incorporación:</td>
        <td>0€</td>
      </tr>
   </table>
<br/>
<div>EVOLUCIÓN DE LAS APORTACIONES</div>
<table style="width:100%">
    <tr>
       <th rowspan="2">Fecha</th>
       <th rowspan="2">Concepto</th>
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

    <tr>
       <td colspan="5">${dades_soci['inversions'][0][1]}</td>
	</tr>
%    for dades_apo_str in dades_soci['inversions']:

<% 
    """
        dades_apo = ast.literal_eval(dades_apo_str)
       <td>${dades_apo['data_compra']}</td>
       <td>${dades_apo['concepte']}</td>
       <td></td>
       <!-- if obligatoria-->
       <td>${dades_apo['import']}</td>
       <!-- else -->
       <!-- <td></td> -->
       <!-- endif -->
       <td></td>
       <!-- if voluntaria -->
       <td>${dades_apo['import']}</td>
       <!-- else -->
       <!-- <td></td> -->
       <!-- endif -->
       <td>total</td>
    """
%>
     </tr>
%    endfor
  </table>
  <div>*rehusable siempre que el importe total de los reembolsos de las aportaciones voluntarias haya superado antes de la petición de reembolso el 10% del capital social anual según el art. 14 de los Estatutosspan</div>
  <br />
  <br />
  <br />
  <br />
  <br />
%endfor
</body>
</html>
