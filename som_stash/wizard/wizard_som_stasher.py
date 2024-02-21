# -*- encoding: utf-8 -*-
from osv import fields, osv
from tools.translate import _
from datetime import datetime
from dateutil.relativedelta import relativedelta


class WizardSomStasher(osv.osv_memory):
    """Wizard to automate the stashing action"""
    _name = 'wizard.som.stasher'

    def _get_default_years(self, cursor, uid, context=None):
        cfg_obj = self.pool.get('res.config')
        return int(
            cfg_obj.get(cursor, uid, "som_stash_years_ago", "6")
        )

    def get_date_limit(self, cursor, uid, context=None):
        years_ago = self._get_default_years(cursor, uid, context)
        date_limit = datetime.today() - relativedelta(years=years_ago)
        return date_limit

    def get_partners_inactive_pol_before_datelimit(self, cursor, uid, date_limit, context=None):
        str_date_limit = datetime.strftime(date_limit, '%Y-%m-%d')

        sql_array = """
            select
            array_agg(gp.titular) as partner_ids
            --gp.titular
            from giscedata_polissa gp
            where
            state = 'baixa'
            and data_baixa <= %s
            and not exists
            (   select gp2.titular
                from giscedata_polissa gp2
                where (gp2.state = 'activa' or (gp2.state = 'baixa' and gp2.data_baixa > %s))
                and gp2.titular = gp.titular
            )
        """
        cursor.execute(sql_array, (str_date_limit, str_date_limit))
        res = cursor.dictfetchone()["partner_ids"]
        return res or []

    def get_partners_inactive_soci_before_datelimit(self, cursor, uid, date_limit, context=None):
        str_date_limit = datetime.strftime(date_limit, '%Y-%m-%d')

        sql_array = """
            select
            array_agg(partner_id) as partner_ids
            --partner_id
            from somenergia_soci ss
            where ss.baixa=true and ss.data_baixa_soci <= %s
        """
        cursor.execute(sql_array, (str_date_limit,))
        res = cursor.dictfetchone()["partner_ids"]
        return res or []

    def get_partners_origin_to_stash(self, cursor, uid, context=None):
        date_limit = self.get_date_limit(cursor, uid, context=context)
        patrner_ids = self.get_partners_inactive_soci_before_datelimit(cursor, uid, date_limit)
        patrner_ids += self.get_partners_inactive_pol_before_datelimit(cursor, uid, date_limit)
        res = list(set(patrner_ids))
        return res

    def get_partners(self, cursor, uid, partner_ids, context=None):
        res = [('res.partner', partner_id) for partner_id in partner_ids]
        return res

    def get_partners_address(self, cursor, uid, partner_ids, context=None):
        obj = self.pool.get("res.partner.address")
        to_stash_ids = obj.search(cursor, uid, [
            ('partner_id', 'in', partner_ids),
        ])
        res = [('res.partner.address', id) for id in to_stash_ids]
        return res

    def get_polisses(self, cursor, uid, partner_ids, context=None):
        obj = self.pool.get("giscedata.polissa")
        to_stash_ids = obj.search(cursor, uid, [
            ('titular', 'in', partner_ids),
        ])
        res = [('giscedata.polissa', id) for id in to_stash_ids]
        return res

    def do_stash_process(self, cursor, uid, ids, context=None):
        # variables temporals
        # years = 6
        som_stash_obj = self.pool.get("som.stash")
        # som_stash_setting_obj = self.pool.get("som.stash.setting")
        models_to_stash = som_stash_obj._get_selectable_models_list(cursor, uid, context=context)

        msg = _("Resultat d'execució del wizard de backup de dades:\n")
        do_stash = self.read(
            cursor, uid, ids, ['do_stash'], context=context
        )[0]['do_stash']

        # explore models to get the data to be stashed
        if do_stash:
            # partners_to_stash = self.get_partners_origin_to_stash(cursor, uid, context=context)
            # # listtup [('model', id), ...]
            # listtup_partners = self.get_partners(
            #     cursor, uid, partners_to_stash, context=context
            # )
            # listtup_partners_address = self.get_partners_address(
            #     cursor, uid, partners_to_stash, context=context
            # )
            # listtup_polisses = self.get_polisses(
            #     cursor, uid, partners_to_stash, context=context
            # )

            # do the stash process
            for model in models_to_stash:
                pass
                # stash_setting_fields = som_stash_setting_obj.search

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
    }

    _defaults = {
        "do_stash": lambda *a: False,
        "years": _get_default_years,
    }


WizardSomStasher()
