<%
    day, stadistica = objects[0].get_company_report_data()
%>
<html>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<head>
    <title>Panel de Control de Som Energia</title>
</head>
<body>
    <br />
    <h1 align="center">Quadre de control General</h1>
    <h2 align="center">Dades actualitzades fins el ${day} inclòs</h2>

    <hr width="100%" align="center" /></br></br>

    % for group, values in sorted(stadistica.items()):
        <table border="1" width="60%" align="center">
            <th colspan="2"> ${group}</th>
               % for descriptor, datos in sorted(values.items()):
               <tr>
                   <td width="70%"> ${descriptor}: </td>
                   <td align="right"> ${datos} </td>
               </tr>
               % endfor
        </table></br>
    % endfor

</body>
</html>
