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

    def get_baixa_blocking_reasons(self, cursor, uid, member_id, context=None):
        if not context:
            context = {}
            
        reasons = []
        
        invest_obj = self.pool.get('generationkwh.investment')
        emi_obj = self.pool.get('generationkwh.emission')
        pol_obj = self.pool.get('giscedata.polissa')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        soci_obj = self.pool.get('somenergia.soci')
        
        today = datetime.today().strftime('%Y-%m-%d')
        res_partner_id = soci_obj.read(cursor, uid, member_id, ['partner_id'])['partner_id'][0]

        baixa = soci_obj.read(cursor, uid, [member_id], ['baixa'])[0]['baixa']

        if baixa:
            reasons.append(_('Ja ha estat donat de baixa anteriorment!'))

        genkwh_emission_ids = emi_obj.search(cursor, uid, [('type','=','genkwh')])
        gen_invest = invest_obj.search(cursor, uid, [('member_id', '=', member_id),
                                                     ('emission_id', 'in', genkwh_emission_ids),
                                                     ('last_effective_date', '>=', today)])
        if gen_invest:
            reasons.append(_('El soci té inversions de generation actives.'))

        aportacions_ids = emi_obj.search(cursor, uid, [('type','=','apo')])
        apo_invest = invest_obj.search(cursor, uid, [('member_id', '=', member_id),
                                                     ('emission_id', 'in', aportacions_ids),
                                                     '|', ('last_effective_date', '=', False),
                                                     ('last_effective_date', '>=', today)])
        if apo_invest:
            reasons.append(_('El soci té aportacions actives.'))

        factures_pendents = fact_obj.search(cursor, uid, [('partner_id', '=', res_partner_id),
                                                          ('state', 'not in', ['cancel', 'paid']),
                                                          ('type', '=', 'out_invoice')])

        if factures_pendents and not context.get('skip_pending_check', False):
            reasons.append(_('El soci té factures pendents.'))
        
        polisses_as_titular = pol_obj.search(cursor, uid,
                                  [('soci', '=', res_partner_id),
                                   ('titular', '=', res_partner_id),
                                   ('state', '!=', 'baixa'),
                                   ('state', '!=', 'cancelada')])
        if polisses_as_titular:
            reasons.append(_('El soci té al menys un contracte vinculat com a soci i titular.'))

        polisses_apadrinades = pol_obj.search(cursor, uid,
                                  [('soci', '=', res_partner_id),
                                   ('titular', '!=', res_partner_id),
                                   ('state', '!=', 'baixa'),
                                   ('state', '!=', 'cancelada')])
        if polisses_apadrinades and not context.get('skip_sponsored_check', False):
            reasons.append(_('El soci té al menys un contracte apadrinat.'))
            
        return reasons

    def do_baixa_soci(self, cursor, uid, member_id, bank_account_id, context=None):
        # - Comprovar si té generationkwh: Existeix atribut al model generation que ho indica. Altrament es poden buscar les inversions.
        # - Comprovar si té inversions vigents: Buscar inversions vigents.
        # - Comprovar si té contractes actius: Buscar contractes vigents.
        # - Comprovar si té Factures pendents de pagament: Per a aquesta comprovació hi ha una tasca feta a la OV que ens pot ajudar feta per en Fran a la següent PR: https://github.com/gisce/erp/pull/7997/files

        """Mètode per donar de baixa un soci."""
        context = context or {}
        
        reasons = self.get_baixa_blocking_reasons(cursor, uid, member_id, context=context)
        if reasons:
            raise osv.except_osv("Error", _('El soci no pot ser donat de baixa!'), '\n'.join(reasons))

        imd_obj = self.pool.get('ir.model.data')
        soci_obj = self.pool.get('somenergia.soci')
        rpa_obj = self.pool.get('res.partner.address')

        today = datetime.today().strftime('%Y-%m-%d')
        res_partner_id = soci_obj.read(cursor, uid, member_id, ['partner_id'])['partner_id'][0]

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

        self._unlink_sponsored_contracts(cursor, uid, res_partner_id, context)
        rpa_obj.unsubscribe_partner_in_members_lists(
            cursor, uid, [res_partner_id], context=context
        )
        self._create_payment_line(cursor, uid, member_id, bank_account_id, context)
        return True

    def _unlink_sponsored_contracts(self, cursor, uid, res_partner_id, context=None):
        polissa_obj = self.pool.get('giscedata.polissa')
        res_partner_obj = self.pool.get('res.partner')

        dni_soci = res_partner_obj.read(cursor, uid, res_partner_id, ['vat'])['vat']
        polisses_apadrinades = polissa_obj.search(cursor, uid, [
            ('soci', '=', res_partner_id), ('titular', '!=', res_partner_id)
        ])
        for polissa_id in polisses_apadrinades:
            polissa_vals = polissa_obj.read(cursor, uid, polissa_id, ['titular', 'name'])
            titular_id = polissa_vals['titular'][0]
            titular_notes = res_partner_obj.read(
                cursor, uid, titular_id, ['comment'])['comment'] or ''
            titular_notes = (
                "{} Contracte {} apadrinat per {},"
                " soci es dona de baixa i treiem apadrinament."
                .format(datetime.now().strftime('%Y-%m-%d'), polissa_vals['name'], dni_soci)
            )
            polissa_obj.write(cursor, uid, polissa_id, {'soci': False})
            res_partner_obj.write(cursor, uid, titular_id, {'comment': titular_notes})

    def _create_payment_line(self, cursor, uid, member_id, bank_account_id, context=None):
        conf_o = self.pool.get("res.config")
        imd_o = self.pool.get("ir.model.data")
        payment_mode_o = self.pool.get("payment.mode")
        payment_order_o = self.pool.get("payment.order")
        currency_o = self.pool.get("res.currency")
        soci_o = self.pool.get("somenergia.soci")
        account_o = self.pool.get("account.account")

        socia_fee_amount = conf_o.get(cursor, uid, "socia_member_fee_amount", "100")
        currency_id = currency_o.search(cursor, uid, [("name", "=", "EUR")])[0]
        payment_mode_id = imd_o.get_object_reference(
            cursor, uid, "som_generationkwh", "soci_return_payment_mode")[1]
        payment_mode_name = payment_mode_o.read(cursor, uid, payment_mode_id, ["name"])["name"]
        payment_order_id = payment_order_o.get_or_create_open_payment_order(
            cursor, uid,  payment_mode_name, use_invoice=False, context=context
        )
        # FIXME: Put the right account code, this is just a test
        acc_id = account_o.search(cursor, uid, [("code", "=", "410000")])[0]
        soci = soci_o.browse(cursor, uid, member_id, context=context)
        self.pool.get("payment.line").create(
            cursor, uid, {
                "name": soci.ref,
                "order_id": payment_order_id,
                "currency": currency_id,
                "partner_id": soci.partner_id.id,
                "company_currency": currency_id,
                "bank_id": bank_account_id,
                "state": "normal",
                "amount_currency": socia_fee_amount,
                "account_id": acc_id,
                "communication": "RETORN QUOTA SOCI",
                "comm_text": "RETORN QUOTA SOCI",
            }
        )

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
