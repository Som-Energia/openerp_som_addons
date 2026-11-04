<%
    from mako.template import Template
    template_id = object.lot_enviament.email_template.id
    backend = object.pool.get('report.backend.mailcanvipreus')
    data = backend.get_campaign_data(object._cr, object._uid, object.id,
        context={'pem_template_id': template_id, 'lang': object.polissa_id.titular.lang})
    def common(xml_id):
        templates = object.pool.get('poweremail.templates')
        model_data = object.pool.get('ir.model.data')
        record_id = model_data.get_object_reference(object._cr, object._uid,
            'som_poweremail_common_templates', xml_id)[1]
        body = templates.read(object._cr, object._uid, record_id,
            ['def_body_text'], context={'lang': data['lang']})['def_body_text']
        return Template(body).render_unicode(object=object)
%>
${common('common_template_header_v2')}
<%include file="warning.mako" args="mail_data=data"/>
<p>Hola${data['nom_titular'] | h} <br/></p>
${data['banners']['CANVI_PREUS_MOTIU']}
<%include file="prices.mako" args="mail_data=data"/>
% if 'CANVI_PREUS_AUTOCONSUM' in data['banners']:
${data['banners']['CANVI_PREUS_AUTOCONSUM']}
% endif
<%include file="estimation.mako" args="mail_data=data"/>
<%include file="legal.mako" args="mail_data=data"/>
${data['banners']['CANVI_PREUS_COMIAT']}
${common('common_template_footer_v2')}
