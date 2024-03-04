# -*- encoding: utf-8 -*-
from osv import fields, osv
from tools.translate import _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from addons import get_module_resource


class WizardSomStasher(osv.osv_memory):
    """Wizard to automate the stashing action"""
    _name = 'wizard.som.stasher'

    def _get_default_years(self, cursor, uid, context=None):
        cfg_obj = self.pool.get('res.config')
        return int(
            cfg_obj.get(cursor, uid, "som_stash_years_ago", "6")
        )

    def get_date_limit(self, cursor, uid, years_ago, context=None):
        date_limit = datetime.today() - relativedelta(years=years_ago)
        return date_limit

    def get_partners_inactive_pol_before_datelimit(self, cursor, uid, date_limit, context=None):
        str_date_limit = datetime.strftime(date_limit, '%Y-%m-%d')

        sql_path = get_module_resource(
            'som_stash',
            'sql',
            'query_partner_pol_expired.sql'
        )

        with open(sql_path, 'r') as sql_file:
            sql = sql_file.read()

        sql_params = {
            'data_limit': str_date_limit,
        }

        cursor.execute(sql, sql_params)
        res = cursor.dictfetchall()
        return res or []

    def get_partners_inactive_soci_before_datelimit(self, cursor, uid, date_limit, context=None):
        str_date_limit = datetime.strftime(date_limit, '%Y-%m-%d')

        sql_path = get_module_resource(
            'som_stash',
            'sql',
            'query_soci_expired.sql'
        )

        with open(sql_path, 'r') as sql_file:
            sql = sql_file.read()

        sql_params = {
            'data_limit': str_date_limit,
        }

        cursor.execute(sql, sql_params)
        res = cursor.dictfetchall()
        return res or []

    def get_partners_origin_to_stash(self, cursor, uid, years_ago, context=None):
        date_limit = self.get_date_limit(cursor, uid, years_ago, context=context)
        par_pols = self.get_partners_inactive_soci_before_datelimit(cursor, uid, date_limit)
        par_soci = self.get_partners_inactive_pol_before_datelimit(cursor, uid, date_limit)

        res = {}
        for par in par_pols:
            if par['partner_id']:
                res[par['partner_id']] = par

        for par in par_soci:
            if not par['partner_id']:
                continue

            if par['partner_id'] in res:
                if res[par['partner_id']]['date_expiry'] < par['date_expiry']:
                    res[par['partner_id']] = par
            else:
                res[par['partner_id']] = par

        return res

    def get_partners_address(self, cursor, uid, partners_to_stash, context=None):
        obj = self.pool.get("res.partner.address")
        address_ids = obj.search(cursor, uid, [
            ('partner_id', 'in', partners_to_stash.keys()),
        ])

        address_datas = obj.read(cursor, uid, address_ids, ['partner_id'])

        res = {}
        for addr_data in address_datas:
            if not addr_data['id']:
                continue

            res[addr_data['id']] = {
                'partner_id': addr_data['partner_id'],
                'date_expiry': partners_to_stash[addr_data['partner_id']]['date_expiry'],
            }
        return res

    def do_stash_process(self, cursor, uid, ids, context=None):
        msg = _("Resultat d'execució del wizard de backup de dades:\n")
        # do not commit
        # import pudb; pu.db
        wiz = self.read(
            cursor, uid, ids, [], context=context
        )[0]

        do_stash = wiz['do_stash']
        limit_to_stash = wiz['limit_to_stash']
        years_ago = max(wiz['years'], 6)

        partners_to_stash = self.get_partners_origin_to_stash(
            cursor, uid, years_ago, context=context
        )

        if limit_to_stash and limit_to_stash < len(partners_to_stash):
            partners_to_stash = partners_to_stash[:limit_to_stash]

        msg += _(
            "Trobats {} partners per fer backup.\nLlista d'Ids:\n{}".format(
                len(partners_to_stash),
                ', '.join([str(i) for i in partners_to_stash.keys()])
            )
        )

        if do_stash and partners_to_stash:
            som_stash_obj = self.pool.get("som.stash")
            res_partners_stashed = som_stash_obj.do_stash(
                cursor, uid,
                partners_to_stash,
                'res.partner',
                context=context
            )

            msg += _(
                "\nModificades {} fitxes de partners.\nLlista d'Ids:\n{}".format(
                    len(res_partners_stashed),
                    ', '.join([str(i) for i in res_partners_stashed if i])
                )
            )

            partners_address_to_stash = self.get_partners_address(
                cursor, uid, partners_to_stash, context=context
            )
            res_partners_address_stashed = som_stash_obj.do_stash(
                cursor, uid,
                partners_address_to_stash,
                'res.partner.address',
                context=context
            )

            msg += _(
                "\nModificades {} fitxes d'adreces de partners.\nLlista d'Ids:\n{}".format(
                    len(res_partners_address_stashed),
                    ', '.join([str(i) for i in res_partners_address_stashed if i])
                )
            )

        self.write(
            cursor, uid, ids, {'info': msg}
        )

    _columns = {
        'info': fields.text('Informació', readonly=True),
        'do_stash': fields.boolean(
            'Modifica',
            help=_('Si la casella esta marcada, es realitzaran canvis als '
                   'regsitres trobats')
        ),
        'years': fields.integer(_("Antiguitat en anys")),
        'limit_to_stash': fields.integer(_("Elements a fet backup (0 = tots)")),
    }

    _defaults = {
        "do_stash": lambda *a: False,
        "years": _get_default_years,
    }


WizardSomStasher()
