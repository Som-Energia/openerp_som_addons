## -*- coding: utf-8 -*-

<%namespace file="account_invoice_som/report/nota_carrec/components/capcalera.mako" import="capcalera"/>
<%namespace file="account_invoice_som/report/nota_carrec/components/detall_nota.mako" import="detall_nota"/>
<%namespace file="account_invoice_som/report/nota_carrec/components/dades_nota.mako" import="dades_nota"/>
<%namespace file="account_invoice_som/report/nota_carrec/components/extra_data.mako" import="extra_data"/>


<!DOCTYPE html>
<html>
    <head>
        <meta http-equiv="content-type" content="text/html; charset=utf-8"/>
        <title>${_(u"NOTA DE CÀRREC/ABONAMENT")}</title>
        <style type="text/css">
            @font-face {
                font-family: "Roboto";
                src: url("${assets_path}/fonts/Roboto/Roboto-Regular.ttf") format('truetype');
                font-weight: normal;
            }
            @font-face {
                font-family: "Roboto";
                src: url("${assets_path}/fonts/Roboto/Roboto-Bold.ttf") format('truetype');
                font-weight: bold;
            }
        </style>
        <link rel="stylesheet" href="${addons_path}/account_invoice_som/report/nota_carrec/style.css"/>
    </head>
    <body>
    %for nota in objects:
        <%
            issuer = nota['issuer']
            recipient = nota['recipient']
            linies = nota['line_info']
            info = nota['info']
            banners = nota['banners']
        %>
        <div class="a4">
            <div class="a4-content">
                <div>
                    ${capcalera(issuer, recipient, banners)}
                </div>
                <div>
                    ${dades_nota(info)}
                </div>
                <div>
                    ${detall_nota(linies, info)}
                </div>
                <div>
                    ${extra_data()}
                </div>
            </div>
        </div>
    %endfor
    </body>
</html>
