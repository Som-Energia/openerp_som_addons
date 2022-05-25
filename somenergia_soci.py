# -*- coding: utf-8 -*-

from __future__ import absolute_import

from osv import osv, fields
from tools.translate import _
from tools import config
from oorq.decorators import job

from datetime import datetime, date

def field_function(ff_func):
    def string_key(*args, **kwargs):
        res = ff_func(*args, **kwargs)
        ctx = kwargs.get('context', None)
        if ctx or ctx is None:
            return res

        if not ctx.get('xmlrpc', False):
            return res

        return dict([(str(key), value) for key, value in res.tuples])

    return string_key


class SomenergiaSoci(osv.osv):
    """ Class to manage GkWh info in User interface"""

    _name = 'somenergia.soci'
    _inherit = 'somenergia.soci'

    @field_function
    def _ff_investments(self, cursor, uid, ids, field_names, args,
                        context=None):
        """ Check's if a member any gkwh investment"""
        invest_obj = self.pool.get('generationkwh.investment')
        kwhpershare_obj = self.pool.get('generationkwh.kwh.per.share')

        if context is None:
            context = {}

        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        init_dict = dict([(f, False) for f in field_names])
        res = {}.fromkeys(ids, {})
        for k in res.keys():
            res[k] = init_dict.copy()

        for member_id in ids:
            investments = invest_obj.effective_investments(
                cursor, uid, member_id, None, None, context=context
            )
            member_data = res[member_id]
            if 'has_gkwh' in field_names:
                member_data['has_gkwh'] = len(investments) > 0
            # Current investments
            total_fields = ['active_shares', 'estimated_anual_kwh']
            if set(total_fields).intersection(field_names):
                today = date.today().strftime('%Y-%m-%d')
                current_investments = invest_obj.effective_investments(
                    cursor, uid, member_id, today, today, context=context
                )
                total_investments = sum([i.shares for i in current_investments])
                if 'active_shares' in field_names:
                    member_data['active_shares'] = total_investments
                if 'estimated_anual_kwh' in field_names:
                    kwhpershare = kwhpershare_obj.get_kwh_per_date(
                        cursor, uid, context=context
                    )
                    total_kwh = kwhpershare * total_investments
                    member_data['estimated_anual_kwh'] = total_kwh

        return res

    def _search_has_gkwh(self, cursor, uid, obj, field_name, args,
                         context=None):
        """ Search has_gkwh members"""
        sql = """SELECT distinct(member_id)
                    FROM generationkwh_investment WHERE emission_id  IN
                    ( SELECT id from generationkwh_emission where type = 'genkwh')"""
        cursor.execute(sql)
        vals = [v[0] for v in cursor.fetchall()]

        return [('id', 'in', vals)]

    def add_gkwh_comment(self, cursor, uid, member_id, text, context=None):
        """ Adds register logs in gkwh_comments"""
        Users = self.pool.get('res.users')

        member_vals = self.read(cursor, uid, member_id, ['gkwh_comments'])

        user_vals = Users.read(cursor, uid, uid, ['name', 'login'])

        header_tmpl = (
            u"\n----- {0} - {1} ------------------------------------\n"
        )
        header = header_tmpl.format(
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            user_vals['name'],
        )
        comment_txt = u"{0}{1}\n".format(header, text)
        comments = comment_txt + (member_vals['gkwh_comments'] or '')

        self.write(cursor, uid, member_id, {'gkwh_comments': comments})
        return comment_txt

    def poweremail_write_callback(self, cursor, uid, ids, vals, context=None):
        """Hook que cridarà el poweremail quan es modifiqui un email
        a partir d'un soci.
        """
        if context is None:
            context = {}

        # super(SomenergiaSoci, self).poweremail_write_callback(
        #     cursor, uid, vals, context=context
        # )

        imd_model = self.pool.get('ir.model.data')
        model, template_id = imd_model.get_object_reference(
            cursor, uid, 'som_generationkwh',
            'generationkwh_assignment_notification_mail'
        )

        if template_id == int(context.get('template_id', '0')):
            for member_id in ids:
                member_vals = {'gkwh_assignment_notified': True}
                self.write(cursor, uid, member_id, member_vals, context=context)

        return True

    @job(queue="mailchimp_tasks")
    def arxiva_socia_mailchimp_async(self, cursor, uid, ids, context=None):
        """
        Archive member async method
        """
        return self.arxiva_socia_mailchimp(cursor, uid, ids, context=context)


    def arxiva_socia_mailchimp(self, cursor, uid, ids, context=None):
        import mailchimp_marketing as MailchimpMarketing
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        MAILCHIMP_CLIENT = MailchimpMarketing.Client(
            dict(api_key=config.options.get('mailchimp_apikey'),
                 server=config.options.get('mailchimp_server_prefix')
            ))

        conf_obj = self.pool.get('res.config')
        res_partner_obj = self.pool.get('res.partner')
        res_partner_address_obj = self.pool.get('res.partner.address')

        list_name = conf_obj.get(
            cursor, uid, 'mailchimp_socis_list', None)

        list_id = res_partner_address_obj.get_mailchimp_list_id(list_name, MAILCHIMP_CLIENT)
        for partner_id in self.read(cursor, uid, ids,['partner_id']):
            address_list = res_partner_obj.read(cursor, uid, partner_id['partner_id'][0], ['address'])['address']
            res_partner_address_obj.archieve_mail_in_list(cursor, uid, address_list, list_id, MAILCHIMP_CLIENT)


    def verifica_baixa_soci(self, cursor, uid, ids, context=None):
        # - Comprovar si té generationkwh: Existeix atribut al model generation que ho indica. Altrament es poden buscar les inversions.
        # - Comprovar si té inversions vigents: Buscar inversions vigents.
        # - Comprovar si té contractes actius: Buscar contractes vigents.
        # - Comprovar si té Factures pendents de pagament: Per a aquesta comprovació hi ha una tasca feta a la OV que ens pot ajudar feta per en Fran a la següent PR: https://github.com/gisce/erp/pull/7997/files

        """Mètode per donar de baixa un soci.
        """
        if not context:
            context = {}
        if not ids:
            return
        if isinstance(ids, (int, long)):
            ids = [ids]
        if len(ids) != 1:
            raise osv.except_osv(_('Com ha minim es necessita un soci'))

        imd_obj = self.pool.get('ir.model.data')
        invest_obj = self.pool.get('generationkwh.investment')
        emi_obj = self.pool.get('generationkwh.emission')
        pol_obj = self.pool.get('giscedata.polissa')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        soci_obj = self.pool.get('somenergia.soci')
        today = datetime.today().strftime('%Y-%m-%d')
        member_id = ids[0]
        res_partner_id = soci_obj.read(cursor, uid, member_id, ['partner_id'])['partner_id'][0]

        baixa = soci_obj.read(cursor, uid, [member_id], ['baixa'])[0]['baixa']

        if baixa:
            raise osv.except_osv(_('El soci no pot ser donat de baixa!'),
                                 _('Ja ha estat donat de baixa anteriorment!'))

        genkwh_emission_ids = emi_obj.search(cursor, uid, [('type','=','genkwh')])
        gen_invest = invest_obj.search(cursor, uid, [('member_id', '=', member_id),
                                                     ('emission_id', 'in', genkwh_emission_ids),
                                                     ('last_effective_date', '>=', today)])
        if gen_invest:
            raise osv.except_osv(_('El soci no pot ser donat de baixa!'),
                                 _('El soci té inversions de generation actives.'))

        aportacions_ids = emi_obj.search(cursor, uid, [('type','=','apo')])
        apo_invest = invest_obj.search(cursor, uid, [('member_id', '=', member_id),
                                                     ('emission_id', 'in', aportacions_ids),
                                                     '|', ('last_effective_date', '=', False),
                                                     ('last_effective_date', '>=', today)])
        if apo_invest:
            raise osv.except_osv(_('El soci no pot ser donat de baixa!'), _('El soci té aportacions actives.'))

        factures_pendents = fact_obj.search(cursor, uid, [('partner_id', '=', res_partner_id),
                                                          ('state', 'not in', ['cancel', 'paid']),
                                                          ('type', '=', 'out_invoice')])
        if factures_pendents:
            raise osv.except_osv(_('El soci no pot ser donat de baixa!'), _('El soci té factures pendents.'))

        polisses = pol_obj.search(cursor, uid,
                                  [('titular', '=', res_partner_id),
                                   ('state', '!=', 'baixa'),
                                   ('state', '!=', 'cancelada')])
        if polisses:
            raise osv.except_osv(_('El soci no pot ser donat de baixa!'), _('El soci té al menys un contracte actiu.'))

        soci_category_id = imd_obj.get_object_reference(
            cursor, uid, 'som_partner_account', 'res_partner_category_soci'
        )[1]

        def delete_rel(cursor, uid, categ_id, res_partner_id):
            cursor.execute('delete from res_partner_category_rel where category_id=%s and partner_id=%s',(categ_id, res_partner_id))

        res_users = self.pool.get('res.users')
        usuari = res_users.read(cursor, uid, uid, ['name'])['name']
        old_comment = soci_obj.read(cursor, uid, [member_id], ['comment'])[0]['comment']
        old_comment = old_comment + '\n' if old_comment else '' 
        comment =  "{}Baixa efectuada a data {} per: {}".format(old_comment, today, usuari)
        soci_obj.write(cursor, uid, [member_id], {'baixa': True,
                                                'data_baixa_soci': today,
                                                'comment': comment })
        delete_rel(cursor, uid, soci_category_id, res_partner_id)

        self.arxiva_socia_mailchimp_async(cursor, uid, member_id)

        return True


    _columns = {
        'has_gkwh': fields.function(
            _ff_investments, string='Te drets GkWh', readonly=True,
            fnct_search=_search_has_gkwh, type='boolean', method=True,
            multi='investments'
        ),
        'active_shares': fields.function(
            _ff_investments, string='Accions actives', readonly=True,
            type='integer', method=True,
            multi='investments'
        ),
        'estimated_anual_kwh': fields.function(
            _ff_investments, string='Previsió de kWh anual', readonly=True,
            type='integer', method=True,
            multi='investments'
        ),
        'investment_ids': fields.one2many(
            'generationkwh.investment', 'member_id', string="Inversions",
            readonly=True,
            context={'active_test': False},
        ),
        'assignment_ids': fields.one2many(
            'generationkwh.assignment', 'member_id', string="Assignacions"
        ),
        'gkwh_assignment_notified': fields.boolean(
            'Assignació per defecte notificada',
            help=u"Indica que ja s'ha notificat l'assignació per defecte. "
                 u"S'activa quan s'envia el mail"
        ),
        'gkwh_comments': fields.text('Observacions'),
    }

    _defaults = {
        'gkwh_assignment_notified': lambda *a: False,
    }

SomenergiaSoci()


class GenerationkWhkWhxShare(osv.osv):

    _name = "generationkwh.kwh.per.share"
    _order = "version_start_date DESC"

    def get_kwh_per_date(self, cursor, uid, date=None, context=None):
        """ Returns kwh on date
        :param date: date of calc. today if None
        :return: kwh per share on date
        """
        if date is None:
            date = datetime.today().strftime("%Y-%m-%d")

        v_ids = self.search(
            cursor, uid, [
                ('version_start_date', '<=', date)
            ], order='version_start_date desc'
        )
        return self.read(cursor, uid, v_ids[0], ['kwh'])['kwh']

    _columns = {
        'version_start_date': fields.date(u"Data Valor"),
        'kwh': fields.integer(u"kWh per acció"),
    }

GenerationkWhkWhxShare()
