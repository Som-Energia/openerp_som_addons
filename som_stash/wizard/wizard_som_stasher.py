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

    def get_o2m_models_to_stash(self, cursor, uid, context=None):
        obj_im = self.pool.get('ir.model')
        res_partner_model_id = obj_im.search(cursor, uid, [
            ('model', '=', 'res.partner'),
        ])[0]

        obj_sss = self.pool.get('som.stash.setting')
        sss_ids = obj_sss.search(cursor, uid, [
            ('model', "!=", res_partner_model_id)
        ])

        list_dict_models = obj_sss.read(cursor, uid, sss_ids, ['model'])
        # list set of dict models
        # [{'model': (73, u'Partner Addresses'), 'id': 26L}, ...]
        list_models = list(set([d['model'] for d in list_dict_models]))
        res = [
            (obj_im.read(cursor, uid, item[0], ['model'])['model'], item[1])
            for item in list_models
        ]

        return res

    def get_o2m_partner_objects(self, cursor, uid, partners_to_stash, model, fk_field, context=None):  # noqa: E501
        obj = self.pool.get(model)
        o2m_ids = obj.search(cursor, uid, [
            (fk_field, 'in', partners_to_stash.keys()),
        ])

        o2m_datas = obj.read(cursor, uid, o2m_ids, [fk_field])

        res = {}
        for o2m_data in o2m_datas:
            if not o2m_data['id']:
                continue

            res[o2m_data['id']] = {
                'partner_id': o2m_data[fk_field][0],
                'date_expiry': partners_to_stash[o2m_data[fk_field][0]]['date_expiry'],
            }
        return res

    def do_stash_o2m_model(self, cursor, uid, partners_to_stash, model_name, model_human_name, fk_field, context=None):    # noqa: E501
        o2m_objects_to_stash = self.get_o2m_partner_objects(
            cursor, uid, partners_to_stash, model_name, fk_field, context=context
        )
        som_stash_obj = self.pool.get("som.stash")
        o2m_objects_stashed = som_stash_obj.do_stash(
            cursor, uid,
            o2m_objects_to_stash,
            model_name,
            context=context
        )

        msg = _(
            "\nModificades {} fitxes {}.\nLlista d'Ids:\n{}".format(
                len(o2m_objects_stashed),
                model_human_name,
                ', '.join([str(i) for i in o2m_objects_stashed if i])
            )
        )

        return msg

    def do_stash_process(self, cursor, uid, ids, context=None):
        msg = _("Resultat d'execució del wizard de backup de dades:\n")
        wiz = self.read(
            cursor, uid, ids, [], context=context
        )[0]

        do_stash = wiz['do_stash']
        limit_to_stash = wiz['limit_to_stash']
        years_ago = max(wiz['years'], 6)

        partners_to_stash = self.get_partners_origin_to_stash(
            cursor, uid, years_ago, context=context
        )

        partner_keys = sorted(partners_to_stash.keys())
        if limit_to_stash and limit_to_stash < len(partner_keys):
            partner_keys = partner_keys[:limit_to_stash]
            res = {}
            for partner_key in partner_keys:
                res[partner_key] = partners_to_stash[partner_key]
            partners_to_stash = res

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

            o2m_models = self.get_o2m_models_to_stash(cursor, uid, context=context)
            fk_field = 'partner_id'
            for t_model in o2m_models:
                model_name = t_model[0]
                model_human_name = t_model[1]
                msg += self.do_stash_o2m_model(
                    cursor, uid,
                    partners_to_stash, model_name, model_human_name, fk_field,
                    context=context,
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
