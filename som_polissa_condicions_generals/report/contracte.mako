<!doctype html public "-//w3c//dtd html 4.0 transitional//en">
<html>
<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
	<head>
		<style type="text/css">
	    ${css}
	    </style>
        <link rel="stylesheet"
              href="${addons_path}/som_polissa_condicions_generals/report/stylesheet_generic_contract.css"/>
        <%block name="custom_css" />

	</head>
    <%
        from datetime import datetime
        from collections import namedtuple
        from giscedata_polissa.report.utils import localize_period, datetime_to_date
        from giscedata_facturacio.report.utils import get_atr_price

        def clean_text(text):
            return text or ''
        comptador_polisses = 0
    %>
	<%def name="clean(text)">
		${text or ''}
	</%def>

    <%def name="enviament(diferent, text)">
        %if not diferent:
            ${clean(text)}
        %endif
    </%def>
<%
    res = {'currency': company.currency_id.id}
    address = company.partner_id.address[0]
    for field in 'street street2 zip city email phone'.split():
        if address[field]:
            res[field] = address[field]
    %>


	<body>
		%for polissa in objects:
            <%
                pool = polissa.pool
                setLang(polissa.pagador.lang)
            %>
            <p style="height: 20px"></p>
        	<div id="header">
                <div style="float:left; width: 25%;">
                    <div id="logo">
                        <img id="logo" src="data:image/jpeg;base64,${company.logo}"/>
                    </div>
                </div>
                <div style="float:left; width: 55%;">
                    <div class="company">
                        ${company.name}
                    </div>
                    <div class="text_capcalera">
                        <%block name="text_capcalera">
                        </%block>
                    </div>
                </div>
                <div style="float:right; width: 20%;">
                    <div class="text_capcalera">
                        <span class="text_vigencia">${_("Vigència")}</span>
                        <br>
                        <%
                            data_inici = ''
                            data_final = ''
                            if 'form' in data.keys():
                                form = data['form']
                                data_inici = form['polissa_date']
                                modcon_obj = pool.get('giscedata.polissa.modcontractual')
                                modcon_id = modcon_obj.search(cursor, uid, [
                                    ('polissa_id', '=', polissa.id),
                                    ('data_inici', '=', data_inici)
                                ], context={'active_test': False})
                                data_final = modcon_obj.read(cursor, uid, modcon_id, ['data_final'])[0]['data_final']
                            else:
                                data_inici = polissa.modcontractual_activa.data_inici
                                data_final = polissa.modcontractual_activa.data_final
                        %>
                        ${_("Des de")}
                        ${formatLang(data_inici, date=True)}
                        <br>
                        ${_("Fins a")}
                        ${formatLang(data_final, date=True)}
                        <br>
                    </div>
                </div>
                <div style="clear:both"></div>
                <div class="titol">
                    ${_("CONDICIONS PARTICULARS DEL CONTRACTE DE SUBMINISTRAMENTS D'ENERGIA ELÈCTRICA DE BAIXA TENSIÓ")}
                </div>
            </div>
            <div class="seccio">
                <%block name="info_titular">
                </%block>
            </div>
        	<div class="seccio">
        		${_("DADES DEL CLIENT")}
        		<br>
                <div>
                    <table style="margin-top: 5px;">
                        <tr>
                            <td style="width: 500px;">
                                <span class="label">${_("Nom/Motiu Social:")}</span>
                                <span class="field">${polissa.titular.name}</span>
                            </td>
                            <td style="width: 250px;">
                                <span class="label">${_("NIF/CIF:")}</span>
                                <span class="field">${polissa.titular and (polissa.titular.vat or '').replace('ES', '')}</span>
                            </td>
                        </tr>
                    </table>
                </div>
                <table style="margin-top: 5px;">
                    <tr>
                        <td style="width: 200px;">
                            <span class="label">${_("CNAE:")}</span>
                            <span class="field">${clean(polissa.cnae.name)}</span>
                        </td>
                    </tr>
                    <tr>
                        <td style="width: 550px;">
                            <span class="label">${_("Activitat Principal:")}</span>
                            <span class="field">${clean(polissa.cnae.descripcio)}</span>
                        </td>
                    </tr>
                </table>
        		<table style="margin-top: -1px;">
                    <% direccio_titular = polissa.titular.address[0] %>
        			<tr>
        				<td colspan="2">
        					<span class="label">${_("Direcció:")}</span>
        					<span class="field">${clean(direccio_titular.street)}</span>
        				</td>
        			</tr>
        			<tr>
        				<td style="width: 500px;">
        					<span class="label">${_("Codi Postal/Població:")}</span>
        					<span class="field">${clean(direccio_titular.zip)} ${clean(direccio_titular.city)}</span>
        				</td>
        				<td style="width: 250px;">
        					<span class="label">${_("Provincia/País:")}</span>
        					<span class="field">${clean(direccio_titular.state_id.name)} ${clean(direccio_titular.country_id.name)}</span>
        				</td>
        			</tr>
        		</table>
        		<table style="margin-top: -1px;">
        			<tr>
        				<td style="width: 250px;">
        					<span class="label">${_("Teléfon:")}</span>
        					<span class="field">${clean(direccio_titular.mobile)}</span>
        				</td>
        				<td style="width: 250px;">
        					<span class="label">${_("Teléfon 2:")}</span>
        					<span class="field">${clean(direccio_titular.phone)}</span>
        				</td>
        				<td style="width: 260px;">
        					<span class="label">${_("Fax:")}</span>
        					<span class="field">${clean(direccio_titular.fax)}</span>
        				</td>
        			</tr>
        			<tr>
        				<td colspan="3">
        					<span class="label">${_("E-Mail:")}</span>
        					<span class="field">${clean(direccio_titular.email)}</span>
        				</td>
        			</tr>
        		</table>
        	</div>
        	<div class="seccio">
                ${_("DADES DEL CONTACTE (Enviament factura, Altres comunicacions... Ometre únicament si no difereix de les dades del client)")}
        		<br>
                <%
                    direccio_envio = polissa.direccio_notificacio
                    diferent = (polissa.direccio_notificacio == direccio_titular)
                %>
        		<table style="margin-top: 5px;">
        			<tr>
        				<td>
        					<span class="label">${_("Nom/Motiu Social:")}</span>
        					<span class="field">${enviament(diferent, direccio_envio.name)}</span>
        				</td>
        			</tr>
        		</table>
        		<table style="margin-top: -1px;">
        			<tr>
        				<td colspan="2">
        					<span class="label">${_("Direcció:")}</span>
        					<span class="field">${enviament(diferent, direccio_envio.street)}</span>
        				</td>
        			</tr>
        			<tr>
        				<td style="width: 500px;">
        					<span class="label">${_("Codi Postal/Població:")}</span>
        					<span class="field">${enviament(diferent,
                                '{0} {1}'.format(
                                    clean_text(direccio_envio.zip), clean_text(direccio_envio.city)
                                )
                            )}</span>
        				</td>
        				<td style="width: 250px;">
        					<span class="label">${_("Provincia/País:")}</span>
        					<span class="field">${enviament(diferent,
                                '{0} {1}'.format(
                                    clean_text(direccio_envio.state_id.name), clean_text(direccio_envio.country_id.name)
                                )
                            )}</span>
        				</td>
        			</tr>
        		</table>
        		<table style="margin-top: -1px;">
        			<tr>
        				<td style="width: 250px;">
        					<span class="label">${_("Teléfon:")}</span>
        					<span class="field">${enviament(diferent,
                                '{0}'.format(
                                    clean_text(direccio_envio.mobile)
                                )
                            )}</span>
        				</td>
        				<td style="width: 250px;">
        					<span class="label">${_("Teléfon 2:")}</span>
        					<span class="field">${enviament(diferent,
                                '{0}'.format(
                                    clean_text(direccio_envio.phone)
                                )
                            )}</span>
        				</td>
        				<td style="width: 260px;">
        					<span class="label">${_("Fax:")}</span>
        					<span class="field">${enviament(diferent,
                                '{0}'.format(
                                    clean_text(direccio_envio.fax)
                                )
                            )}</span>
        				</td>
        			</tr>
        			<tr>
        				<td colspan="3">
        					<span class="label">${_("E-Mail:")}</span>
        					<span class="field">${enviament(diferent,
                                '{0}'.format(
                                    clean_text(direccio_envio.email)
                                )
                            )}</span>
        				</td>
        			</tr>
        		</table>
        	</div>
        	<div class="titol">
        		${_("CONDICIONS TÉCNIC-ECONÓMIQUES")}
        	</div>
        	<div class="seccio">
        		${_("DADES DEL PUNT DE SUBMINISTRAMENT (Ometre únicament si no difereix de les dades del client)")}
                <%
                    direccio_ps = polissa.cups
                    direccio_cups = polissa.cups_direccio
                    idx_pob = direccio_cups.rfind('(')
                    if idx_pob != -1:
                        direccio_cups = direccio_cups[:idx_pob]
                %>
        		<br>
        		<table style="margin-top: 5px;">
        			<tr>
        				<td colspan="4">
        					<span class="label">${_("Direcció:")}</span>
        					<span class="field">${direccio_cups}</span>
        				</td>
        			</tr>
        			<tr>
        				<td style="width: 68%;">
        					<span class="label">${_("Codi Postal/Població:")}</span>
        					<span class="field">${clean(direccio_ps.dp)} ${clean(direccio_ps.id_poblacio.name)}</span>
        				</td>
        				<td style="width: 32%;" >
        					<span class="label">${_("Provincia/País:")}</span>
        					<span class="field">${clean(direccio_ps.id_provincia.name)} ${clean(direccio_ps.id_provincia.country_id.name)}</span>
        				</td>
        			</tr>
                </table>
                <table style="margin-top: 5px;">
        			<tr>
                        <td>
        					<span class="label">${_("Ref.Catastral:")}</span>
        					<span class="field">${polissa.cups.ref_catastral}</span>
        				</td>
                    </tr>
                    <tr>
        				<td>
        					<span class="label">${_("CUPS:")}</span>
        					<span class="field">${polissa.cups.name}</span>
        				</td>
        				<td>
        					<span class="label">${_("Contracte Nº:")}</span>
        					<span class="field">${clean(polissa.name)}</span>
        				</td>
        			</tr>
                </table>
                <table style="margin-top: 5px;">
        			<tr>
        				<td style="width: 68%;">
        					<span class="label">${_("Empresa Distribuidora:")}</span>
        					<span class="field">${clean(polissa.distribuidora.name)}</span>
        				</td>
        				<td style="width: 32%;">
        					<span class="label">${_("Tensió Nominal(V):")}</span>
        					<span class="field">${clean(polissa.tensio)}</span>
        				</td>
        			</tr>
        		</table>
        	</div>
        	<div class="seccio">
        		${_("TARIFA D'ACCÈS (Definides al R.D. 1164/2001 del 26 de octubre de 2001):")}
        		<br>
        		<table style="margin-top: 5px;">
        			<tr>
        				<td style="width: 100px;">
        					<span class="label">${_("Tarifa:")}</span>
        					<span class="field">${clean(polissa.tarifa_codi)}</span>
        				</td>
                        <td style="width: 350px;">
        					<span class="label">${_("Potència Contractada(kW):")}</span>
        					<span class="field">${clean(polissa.potencia)}</span>
        				</td>
        			</tr>
                </table>
                <table style="margin-top: 5px;">
        			<%
                            potencies = polissa.potencies_periode
                            periodes = []
                            for i in range(0, 6):
                                if i < len(potencies):
                                    periode = potencies[i]
                                else:
                                    periode = False
                                periodes.append((i+1, periode))
                        %>
                    <tr>
                        %for p in periodes:
                            <td style="width: 60px;">
                                <span class="label">${"P{0}".format(p[0])}</span>
                                <span class="field">${p[1] and p[1].potencia or ' '}</span>
                            </td>
                        %endfor
                    </tr>
                </table>

                <table style="margin-top: 5px;">
                    <tr>
                        <td style="width: 100px;">
                            % if polissa.contract_type == '09':
                                <span class="label">${_("Eventual tipus alçat, consum pactat:")}</span>
                                <span class="field">${polissa.expected_consumption} kWh</span>
                            % endif
                        </td>
                    </tr>
                </table>

        	</div>
            ${self.llista_preus(polissa)}
        	<div class="seccio">
        		${_("PRODUCTE CONTRACTAT AMB ")}
				${company.name}:
				<!-- GET COMPANY NAME AQUI -->
        		<br>
        		<table style="margin-top: 5px;">
        			<tr>
        				<td style="width: 150px;">
        					<span class="label">${_("Producte:")}</span>
        					<span class="field">${polissa.llista_preu.name}</span>
        				</td>
                        <%
                            have_lloguer = False
                            have_meters = False
                            if polissa.comptadors:
                                have_meters = True
                                for meter in polissa.comptadors:
                                    if meter.active and meter.lloguer:
                                        have_lloguer = True
                        %>
                        %if have_lloguer:
                            <%block name="info_lloguer">
                            </%block>
                        %endif
                        %if have_meters:
                            <td style="width: 250px;">
                                <span class="label">${_("N. Sèrie equip de mesura:")}</span>
                                <span class="field">${polissa.comptadors[0].name}</span>
                            </td>
                        %endif
        			</tr>
        		</table>
        	</div>
        	<div class="seccio">
        		${_("DADES DEL PAGADOR:")}
        		<br>
        		<table style="margin-top: 5px;">
        			<tr>
        				<td style="width: 60%;">
                            <%
                            owner_b = ''
                            if polissa.bank.owner_name:
                                owner_b = polissa.bank.owner_name
                            %>
        					<span class="label">${_("Titular del Compte:")}</span>
        					<span class="field">${owner_b}</span>
        				</td>
        				<td style="width: 40%;">
        					<span class="label">${_("NIF.:")}</span>
                            <%
                                nif = ''
                                bank_obj = pool.get('res.partner.bank')
                                field = ['owner_id']
                                exist_field = bank_obj.fields_get(
                                    cursor, uid, field)
                                if exist_field:
                                    owner = polissa.bank.owner_id
                                    if owner:
                                        nif = owner.vat or ''
                                    nif = nif.replace('ES', '')
                            %>
        					<span class="field">${nif}</span>
        				</td>
        			</tr>
        		</table>
        		<table style="margin-top: -1px;">
                    <% iban = polissa.bank and polissa.bank.iban[4:] or '' %>
        			<td style="width: 100px;">
    					<span class="label">${_("Entitat Financera:")}</span>
    					<span class="field">${iban[0:4]}</span>
    				</td>
    				<td style="width: 100px;">
    					<span class="label">${_("Sucursal:")}</span>
    					<span class="field">${iban[4:8]}</span>
    				</td>
    				<td style="width: 100px;">
    					<span class="label">${_("DC:")}</span>
    					<span class="field">${iban[8:10]}</span>
    				</td>
    				<td style="width: 100px;">
    					<span class="label">${_("Nº Compte:")}</span>
    					<span class="field">${iban[10:]}</span>
    				</td>
        		</table>
        	</div>
        	<div id="legal">
                <%block name="text_legal">
                    <p>
                    </p>
                </%block>
            </div>
            <div id="footer">
                <div class="city_date">
                    <%
                        if polissa.modcontractual_activa and polissa.modcontractual_activa.data_inici:
                            data_firma =  datetime.strptime(polissa.modcontractual_activa.data_inici, '%Y-%m-%d')
                        elif polissa.data_firma_contracte:
                            data_firma =  datetime.strptime(datetime_to_date(polissa.data_firma_contracte), '%Y-%m-%d')
                        else:
                            data_firma =  datetime.today()
                    %>
                    ${company.partner_id.address[0]['city']}
                    ${_(", a {0}".format(localize_period(data_firma,polissa.pagador.lang or 'es_ES' )))}
                </div>
                <div style="clear:both"></div>
                <div class="signatura">
                    <div style="position:absolute; top: 0px; min-width:100%;">${_("EL CLIENT")}</div>
                    <div style="position:absolute; top: 100px; bottom: 0px; min-width:100%;">Fdo.- ${polissa.titular.name}</div>
                </div>
                <div class="signatura">
                    <div style="position:absolute; top: 0px; min-width:100%;">${company.name}</div>
                    <%block name="signatura_img">
                        <img src="${addons_path}/som_polissa_condicions_generals/report/assets/signatura_contracte.png" style="height:80px" >
                    </%block>
                    <div style="position:absolute; top: 100px; bottom: 0px; min-width:100%;">Fdo.-
                        <%block name="signatura_firmant"/>
                    </div>
                </div>
                <div class="observacions">
                    ${polissa.print_observations or ""}
                </div>
            </div>
            <%
            comptador_polisses += 1;
            %>
            % if comptador_polisses<len(objects):
                <p style="page-break-after:always"></p>
            % endif
        %endfor
	</body>
</html>
<%def name="llista_preus(polissa)"/>
