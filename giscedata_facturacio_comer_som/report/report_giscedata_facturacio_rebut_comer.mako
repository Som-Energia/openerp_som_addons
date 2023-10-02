<%
    from datetime import datetime, timedelta
    from bankbarcode.cuaderno57 import Recibo507
    import numbertoletters
    import nombrestolletres

    pool = objects[0].pool
    fact_obj = pool.get('giscedata.facturacio.factura')
    def clean(text):
        return text or ''

    def localize_period(period, locale):
        if period:
            import babel
            from datetime import datetime
            dtf = datetime.strptime(period, '%Y-%m-%d')
            dtf = dtf.strftime("%y%m%d")
            dt = datetime.strptime(dtf, '%y%m%d')
            return babel.dates.format_datetime(dt, 'd LLLL Y', locale=locale)
        else:
            return ''

%>
<!doctype html public "-//w3c//dtd html 4.0 transitional//en">
<html>
<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
    <head>
        <style type="text/css">
            body{
                font-family: "Liberation Sans";
                font-size: 11px;
                margin-right: 50px;
                margin-left: 50px;
            }
            table{
                font-size: 10px;
                width: 98%;
                float: right;
                border-collapse: collapse;
                border: 0px;
            }
            table td{
                padding-left: 5px;
                padding-right: 5px;
            }
            table td.titol{
                font-size: 7px;
                border-top: 1px solid black;
                border-left: 1px solid black;
                border-right: 1px solid black;
            }
            table td.field{
                border-bottom: 1px solid black;
                border-left: 1px solid black;
                border-right: 1px solid black;
                font-weight: bold;
                font-size: 12px;
            }
            table td.field_blank{
                font-weight: bold;
                font-size: 12px;
            }
            table td.field_bottom{
                border-bottom: 1px solid black;
                font-weight: bold;
                font-size: 12px;
            }
            table td.bold_clear{
                font-weight: bold;
                font-size: 12px;
            }
            #logo{
                position: relative;
                float: left;
                width: 10%;
                height: 400px;
            }
            #img_logo{
                position: relative;
                -ms-transform: rotate(-90deg); /* IE 9 */
                -webkit-transform: rotate(-90deg); /* Chrome, Safari, Opera */
                transform: rotate(90deg);
                left: -110px;
                top: 105px;
                height: 100px;
            }
            #rebut{
                position: relative;
                float: left;
                height: 400px;
                width: 90%;
            }
            .bank_table{
                border-bottom: 1px solid black;
                border-left: 1px solid black;
                border-right: 1px solid black;
            }
            #adreca{
                position: relative;
                top: 20px;
                float: left;
                width: 380px;
                left: 5px;
            }
            #signatura{
                position: relative;
                top: 20px;
                float: left;
                left: 15px;
                width: 220px;
            }
            .space{
                margin-top: 25px;
            }
            ul {
                list-style: none;
                margin-left:10px;
                padding:0px;
            }
            ul li:before {
                color: #000000;
                content: '» ';
                font-size: 1.2em;
                font-weight: bold;
            }
            ${css}
        </style>
    </head>
    <body>
        <%
            i = 1
        %>
        %for fact in objects:
            <%
                setLang(fact.lang_partner)
                entity = ''.join([c for c in fact.polissa_id.comercialitzadora.vat if c.isdigit()])
                datetime.now() + timedelta(days=15)
                #due_date = str(fact.date_due) # data venciment factura
                due_date = datetime.strftime(datetime.now() + timedelta(days=15),'%Y-%m-%d')
                if due_date:
                    suffix = '501'
                    due_date = datetime.strftime(datetime.now() + timedelta(days=15),'%Y-%m-%d')
                else:
                    suffix = '001'
                    due_date = None
                ref = '{}'.format(fact.id).zfill(11) # id factura
                notice = '000000'
                amount = '{0:.2f}'.format(fact.residual) # amount factura
                recibo507 = Recibo507(entity, suffix, ref, notice, amount, due_date)
                notice = recibo507.notice
                ref = ref + recibo507.checksum()
            %>
            <div id="logo">
                <img id="img_logo" src="data:image/jpeg;base64,${company.logo}" >
            </div>
            <div id="rebut">
                <table class="space">
                    <tr>
                        <td class="titol">${_(u"ENTITAT EMISORA")}</td>
                        <td class="titol">${_(u"Nº DE REFERENCIA")}</td>
                        <td class="titol">${_(u"IDENTIFICACIÓ")}</td>
                    </tr>
                    <tr>
                        <td class="field">${ entity }${ suffix }</td>
                        <td class="field">${ ref }</td>
                        <td class="field">${ notice }</td>
                    </tr>
                    <tr>
                        <td class="titol" style="width: 90px;">${_(u"DATA EMISSIÓ")}</td>
                        <td class="titol">${_(u"Document vàlid fins a:")}</td>
                        <td class="titol" style="width: 120px;">${_(u"IMPORT TOTAL Euros")}</td>
                    </tr>
                    <tr>
                        % if fact.lang_partner == 'ca_ES':
                            <td class="field" style="width: 50%;">${localize_period(datetime.now().strftime("%Y-%m-%d"), 'ca_ES')}</td>
                            <td class="field">${localize_period(due_date or False, 'ca_ES')}</td>
                            <td class="field" style="text-align: right;">${formatLang(amount_grouped(fact, 'residual'), monetary=True)}</td>
                        % else:
                            <td class="field" style="width: 50%;">${localize_period(datetime.now().strftime("%Y-%m-%d"), 'es_ES')}</td>
                            <td class="field">${localize_period(due_date or False, 'es_ES')}</td>
                            <td class="field" style="text-align: right;">${formatLang(amount_grouped(fact, 'residual'), monetary=True)}</td>
                        % endif
                    </tr>
		</table>
                <table class="space">
                    <tr>
                        <td class="field_bottom" style="width: 150px;">${_(u"Factura Nº:")}
                        % if fact.group_move_id:
                            ${fact.group_move_id.ref}
                        % else:
                             ${fact.number or ''}
                        % endif
                        </td>
                        <td class="field_bottom">${_(u"Data Factura:")}&emsp;${fact.date_invoice}</td>
                        <td class="field_bottom">${_(u"Contracte:")}&emsp;${fact.polissa_id.name}</td>
                    </tr>
                    <tr>
                        % if fact.group_move_id:
                            <td class="field">${fact.group_move_id.ref}</td>
                        % elif fact.number:
                            <td class="field">${fact.number}</td>
                        % else:
                            <td class="field"></td>
                        % endif
                        <td class="field">Girona</td>
                        <td class="field" style="text-align: right;">${formatLang(amount_grouped(fact, 'residual'), monetary=True)}</td>
                    </tr>
                </table>
                <table>
                    <tr>
			<td></td>
                        <td class="field_bottom" style="width: 65px;">${_(u"EUROS")}</td>
                        <td class="field_bottom">
                            % if fact.lang_partner == 'es_ES':
                                ${numbertoletters.number_to_letters(amount_grouped(fact, 'residual')).upper()}
                            % elif fact.lang_partner == 'ca_ES':
                                ${nombrestolletres.number_to_letters(amount_grouped(fact, 'residual')).upper()}
                            % else:
                                ${amount_grouped(fact, 'residual')}
                            % endif
                        </td>
                    </tr>
                </table>
                <div style="clear:both"></div>
                <div id="adreca">
                    <table style="border: 1px solid black;">
                        <tr>
                            <td>${_(u"NOM I DOMICILI DEL PAGADOR")}</td>
                        </tr>
                        <tr>
                            <td class="field_blank">
                            %if fact.partner_id:
                                ${fact.partner_id.name}
                            %elif fact.partner_bank.partner_id:
                                ${fact.partner_bank.partner_id.name}
                            %endif
                            </td>
                        </tr>
                        <tr>
                            <td class="field_blank">
                            %if fact.partner_id.address:
                                ${fact.partner_id.address[0].street}
                            %elif fact.partner_bank.partner_id:
                                ${fact.partner_bank.partner_id.address[0].street}
                            %endif
                            </td>
                        </tr>
                        <tr>
                            <td class="field_blank">
                            %if fact.partner_id.address[0].zip:
                                ${fact.partner_id.address[0].zip}&emsp;${fact.partner_id.address[0].state_id.name}
                            %elif fact.partner_bank.partner_id.address[0].zip:
                                ${fact.partner_bank.partner_id.address[0].zip}&emsp;${fact.partner_bank.partner_id.address[0].state_id.name}
                            %else:
                                ${fact.partner_id.address[0].state_id.name}
                            %endif
                            </td>
                        </tr>
                    </table>
                <table>
                    <tr>
                        <td>
                        </td>
                    </tr>
                </table>


                </div>
                <div id="signatura">
                    <i>
                        ${fact.polissa_id.comercialitzadora.name}
                        <br>
                    </i>
                </div>
                <div style="clear:both"></div>
                <table class="space">
                    <tr>
                        <td align="center">
                        ${ recibo507.svg(writer_options={
                            'background':'transparent',
                            'module_height': 7,
                            'font_size': 7,
                            'text_distance': 3,
                            'module_width': 0.25})
                        }
                        </td>
                    </tr>
                    <tr>
			<td align="center">
                            ${_(u"Per fer el pagament online, pots entrar a <a href='https://www2.caixabank.es/apl/pagos/index_ca.html?IMP_codigoBarras={recibo507}'>https://www2.caixabank.es/apl/pagos/index_ca.html</a>").format(recibo507=recibo507.code())}
                        </td>
                    </tr>
                </table>
            </div>
            % if fact.group_move_id:
                % if fact.group_move_id:
                    <h3>${_(u"Resum factures agrupades")}:</h3>
                    <ul>
                        <%
                            inv_ids = [l.invoice.id for l in
                                            fact.group_move_id.line_id if l.invoice]
                            fact_ids = fact_obj.search(
                                cursor, uid, [('invoice_id', 'in', inv_ids)])
                        %>
                        % for l in fact_obj.browse(cursor, uid, fact_ids):
                            <li>
                                <%
                                    sentit = 1.0
                                    if l.type in['out_refund', 'in_refund']:
                                        sentit = -1.0
                                    if l.tipo_rectificadora in ['A', 'B', 'BRA']:
                                        text = ' (Factura abonadora de la factura {0})'.format(
                                            l.ref.number or '')
                                    elif l.tipo_rectificadora in ['R', 'RA']:
                                        text = ' (Factura rectificadora de la factura {0})'.format(
                                            l.ref.number or '')
                                    else:
                                        text = ''
                                %>
                                ${l.number} total: ${formatLang(sentit * l.residual, monetary=True)} &euro; ${text}
                            </li>
                        % endfor
                    </ul>
                % endif
                <h3><strong>Total: ${formatLang(amount_grouped(fact, 'residual'), monetary=True)} &euro;</strong></h3>
            % endif
            % if i < len(objects):
                <div style="clear: both;"></div>
                <p style="page-break-after:always"></p>
            % endif
            <%
                i += 1
            %>
        %endfor
    </body>
</html>
