<%
    from collections import Counter
    from datetime import datetime, timedelta
    from bankbarcode.cuaderno57 import Recibo507
    from operator import attrgetter, itemgetter
    from babel.numbers import format_currency

    from giscedata_facturacio_comer.report.utils import  get_line_discount,get_giscedata_fact,get_other_info,get_distri_phone,get_discounts,get_historics
    from account_invoice_base.report.utils import localize_period
    import json, re

    pool = objects[0].pool
    polissa_obj = objects[0].pool.get('giscedata.polissa')
    fact_obj =  objects[0].pool.get('giscedata.facturacio.factura')

    def merge_two_dicts(x, y):
        z = x.copy()   # start with x's keys and values
        z.update(y)    # modifies z with y's keys and values & returns None
        return z
%>
<!doctype html public "-//w3c//dtd html 4.0 transitional//en">
<html>
    <head>
        <meta http-equiv="content-type" content="text/html; charset=utf-8"/>
        <link rel="stylesheet" href="${addons_path}/account_invoice_som/report/bootstrap.css"/>
        <link rel="stylesheet" href="${addons_path}/account_invoice_som/report/stylesheet_account_invoice_som.css"/>
        <title> ${_("Factura SomEnergia")} </title>
    </head>
    <body>
        <%
            counter = 0
        %>
        %for inv in objects:
            <%
                setLang(inv.partner_id.lang)
                sentido = 1.0
                if inv.type in['out_refund', 'in_refund']:
                    sentido = -1.0
                entidad_bancaria = ''
                bank_acc = ''
                if inv.payment_type:
                    if inv.payment_type.code == 'RECIBO_CSB':
                        if not inv.partner_bank:
                            raise Exception(
                                u'La factura {0} no tiene número de cuenta definido.'.format(
                                inv.number)
                            )
                        else:
                            entidad_bancaria = inv.partner_bank.name or inv.partner_bank.bank.lname
                            bank_acc = inv.partner_bank.iban[:-4].replace(' ','')  + '****'
	        elif inv.payment_type.code == 'N57':
		    fact_id = fact_obj.search(cursor, uid, [('invoice_id','=',inv.id)])[0]
		    fact = fact_obj.browse(cursor, uid, fact_id)
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

                else:
                    if inv.partner_bank:
                        entidad_bancaria = inv.partner_bank.name or inv.partner_bank.bank.lname
                        bank_acc = inv.partner_bank.iban[:-4].replace(' ','') + '****'
                altres_lines = [l for l in inv.invoice_line]
                residual_total = inv.residual
                base = 0.0
                total_iese = 0.0
                total_iva = 0.0
                iva_dict = {}
                base_imponible = 0.0
                due_date = str(inv.date_due) # plazo pago = fecha factura + payment_term
                for t in inv.tax_line :
                    if 'especial sobre la electricidad'.upper() in t.name.upper():
                        base +=  t.base
                        total_iese += t.amount
                    elif 'IVA' in t.name.upper():
                        total_iva += t.amount
                        base_imponible += sentido * t.base
                        iva_dict[t.name] = t.base
            %>
            <div id="outer">
                <p id="vertical_text">
                    ${_("SOM ENERGIA SCCL Amb seu social a CL. C/ Riu Güell, 68 · 17005 - Girona - Inscrita al Registre General de Cooperatives, full 13936, Inscripció 1a CIF: F55091367")}
                </p>
            </div>
            <div id="header" class="row-fluid">
                <div id="logo_direccio" class="span5 offset1">
                    <img class="logo" src="data:image/jpeg;base64,${company.logo}"/>
                    <div id="dades_empresa">
                        <%
                            phone = company.partner_id.address[0].phone
                            fax = company.partner_id.address[0].fax
                            email = company.partner_id.address[0].email
                            website = company.partner_id.website
                            company_address = company.partner_id.address[0].street
                            company_address2 = company.partner_id.address[0].city + ' ' + company.partner_id.address[0].zip
                        %>
                        <b> ${company.partner_id.name or ''} </b>
                        ${_("CIF:")} ${company.partner_id.vat or ''}
                        ${_("Domicili:")} ${company_address}
                        ${company_address2}
                        ${email}
                    </div>
                </div>

                <%
                    dades_client = inv.address_invoice_id
                    nom_client = dades_client.name or ''

                    poblacio_client = ''
                    provincia_client = ''

                    if dades_client.id_poblacio:
                        poblacio_client = dades_client.id_poblacio.name or ''
                    if dades_client.state_id:
                        provincia_client = dades_client.state_id.name or ''
                    partner_vat = inv.partner_id.vat
                %>

                <div id="dades_factura" class="span5">
                    <div class="title black">
                        <h2>
                            ${_("DADES DE LA FACTURA")}
                        </h2>
                    </div>
                    <div class="content intro">${("Núm. de factura:")} ${inv.number or ''}
                        ${_("Data:")} ${inv.date_invoice}

                        ${_("Nom:")} ${nom_client}
                        ${_("NIF/CIF:")} ${partner_vat or ''}
                        ${_("Adreça:")} ${dades_client.street or ''} ${poblacio_client} ${provincia_client} ${dades_client.zip or ''}
                    </div>
                </div>
            </div>

            <div id="concepte_factura" class="row-fluid">
                <div class="title dark_gray span10 offset1">
                    <div class="row-fluid">
                        <div class="span1">
                            <h2 class="center"> ${_("Unitats")} </h2>
                        </div>
                        <div id="" class="span7">
                            <h2> ${_("Concepte")} </h2>
                        </div>
                        <div class="span2">
                            <h2 class="center"> ${_("Preu unitari")} </h2>
                        </div>
                        <div class="">
                            <h2 class="right pr_20"> ${_("Import")} </h2>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row-fluid">
                <div id="conceptes" class="span10 offset1">
                    <div class="quantity_section">
                        %for i in sorted(altres_lines):
                            <div class="preu_concepte center">
                                ${formatLang(i.quantity, 2)}
                            </div>
                        %endfor
                    </div>
                    <div id="concept_section" class="">
                        %for i in sorted(altres_lines):
                            <div class="concepte">
                                ${i.name}
                            </div>
                        %endfor
                    </div>
                    <div class="subprice_section">
                        %for i in sorted(altres_lines):
                            <div class="concepte">
                                ${format_currency(float(i.price_unit), 'EUR', locale='es_ES')}
                            </div>
                        %endfor
                    </div>
                    <div class="price_section">
                        %for i in sorted(altres_lines):
                            <div class="preu_concepte">
                                ${format_currency(float(i.price_subtotal), 'EUR', locale='es_ES')}
                            </div>
                        %endfor
                    </div>
                </div>
            </div>

            <div class="row-fluid">
                <div id="totals" class="span10 offset1">
                    <table class="taules_finals">
                        <tr>
                            <td class="black white_font">
                                ${_("Base")}
                            </td>
                            <td class="black white_font">
                                ${_("Impost")}
                            </td>
                            <td class="black white_font">
                                ${_("Quota")}
                            </td>
                            <td class="olivian_green white_font">
                                ${_("TOTAL")}
                            </td>
                        </tr>
                        % for impost in inv.tax_line:
                            <tr>
                                <td class="black_font light_gray">
                                    <div class="preu_final">
                                        ${format_currency(float(impost.base), 'EUR', locale='es_ES')}
                                    </div>
                                </td>
                                <td class="">
                                    <div class="preu_final light_gray">
                                        ${impost.name}
                                    </div>
                                </td>
                                <td class="">
                                    <div class="preu_final light_gray">
                                        ${format_currency(float(impost.factor_amount), 'EUR', locale='es_ES')}
                                    </div>
                                </td>
                                <td class="">
                                    <div class="preu_final light_gray">
                                        ${format_currency(float(impost.base + impost.factor_amount), 'EUR', locale='es_ES')}
                                    </div>
                                </td>
                            </tr>
                        % endfor
                        <tr>
                            <td class="black_font">
                                <div class="preu_final">
                                </div>
                            </td>
                            <td class="">
                                <div class="preu_final">
                                </div>
                            </td>
                            <td class="">
                                <div class="preu_final">
                                </div>
                            </td>
                            <td class="">
                                <div class="preu_final gray">
                                    ${format_currency(float(inv.amount_total), 'EUR', locale='es_ES')}
                                </div>
                            </td>
                        </tr>
                    </table>
                </div>
            </div>

            <div class="row-fluid">
                <div id="totals" class="span10 offset1">
                    <table class="taules_finals">
                        <tr>
                            <td class="black white_font">
                                <h2 class="ta_l title">${_("MÈTODE DE PAGAMENT")} </h2>
                            </td>
                        </tr>
                    </table>
                    <div class="normal_text">

                        %if inv.payment_type.code == 'RECIBO_CSB':
                            <p style="font-size: .8em">${_(u"L'import d'aquesta factura es carregarà al teu compte. El seu pagament quedarà justificat amb l'apunt bancari corresponent")}</p>
                            <p class="center"><b>${bank_acc}</b></p>
                        %elif inv.payment_type.code == 'N57' :
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
                                    ${_("Per fer el pagament online, pots entrar a <a href='https://www.caixabank.es/particular/pagos/impuestosrecibosmatriculas_ca.html'>https://www.caixabank.es/particular/pagos/impuestosrecibosmatriculas_ca.html</a>")}
                                    </td>
                                </tr>
                            </table>

                        %elif inv.payment_type.code == "COBRAMENT_TARGETA":
                            ${_("L'import d'aquesta factura s'ha de pagat mitjançant tarjeta de crèdit")}
			            %else:
                            ${_("L'import d'aquesta factura s'ha de pagar mitjançant transferència bancària al compte indicat:")}
                            <%
                                bank_list = company.partner_id.bank_ids
                                default_bank = next((x for x in bank_list if x.default_bank), None)
                            %>
                        <p class="center"><b>${default_bank.printable_iban}</b> (${default_bank.bank.name})</p>
                        %endif

                    </div>
                </div>
            </div>


            <%
                counter += 1
            %>
            %if counter < len(objects):
                <!-- Si queden factures per imprimir, forçem nou salt de pàgina -->
                <p style="page-break-after:always"></p>
            %endif
        %endfor
    </body>
</html>
