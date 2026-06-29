## -*- coding: utf-8 -*-
<%namespace file="som_polissa_condicions_generals/report/components/summary_header.mako" import="summary_header"/>
<%namespace file="som_polissa_condicions_generals/report/components/summary_identification.mako" import="summary_identification"/>
<%namespace file="som_polissa_condicions_generals/report/components/summary_offer.mako" import="summary_offer"/>
<%namespace file="som_polissa_condicions_generals/report/components/summary_payment.mako" import="summary_payment"/>
<%namespace file="som_polissa_condicions_generals/report/components/summary_discounts.mako" import="summary_discounts"/>
<%namespace file="som_polissa_condicions_generals/report/components/summary_legal.mako" import="summary_legal"/>
<%namespace file="som_polissa_condicions_generals/report/components/summary_claims_cnmc.mako" import="summary_claims_cnmc"/>

<!DOCTYPE html>
<html lang="es">
    <meta http-equiv="content-type" content="text/html; charset=utf-8" />
    <head>
        <style>
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
        <link rel="stylesheet" href="${addons_path}/som_polissa_condicions_generals/report/contract_summary_puppeteer.css"/>
    </head>
    <body>
        %for informe in objects:
            <div class="a4">
                ${summary_header(informe['company'])}
                ${summary_identification(informe['company'], informe['holder'], informe['supply'], informe['self_consumption'])}
                ${summary_offer(informe['offer'], informe['prices'], informe['features'], informe['gurb'])}
                ${summary_payment(informe['payment'])}
                ${summary_discounts(informe['discounts'])}
                ${summary_legal(informe['features'], informe['bono_social_estimate'])}
                ${summary_claims_cnmc(informe['cnmc'])}
            </div>
        %endfor
    </body>
</html>
