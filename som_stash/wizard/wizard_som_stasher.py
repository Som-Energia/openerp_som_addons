# -*- encoding: utf-8 -*-
from osv import fields, osv
from tools.translate import _
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json


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
            and titular is not null
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
        res = sorted(list(set(patrner_ids)))
        return res

    def get_partners_address(self, cursor, uid, partner_ids, context=None):
        obj = self.pool.get("res.partner.address")
        to_stash_ids = obj.search(cursor, uid, [
            ('partner_id', 'in', partner_ids),
        ])
        return to_stash_ids

    def get_polisses(self, cursor, uid, partner_ids, context=None):
        obj = self.pool.get("giscedata.polissa")
        to_stash_ids = obj.search(cursor, uid, [
            ('titular', 'in', partner_ids),
        ])
        return to_stash_ids

    def do_stash_model(self, cursor, uid, ids, model, context=None):

        def make_stasheable_dict(dict):
            time_stamp = datetime.strftime(datetime.today(), '%Y-%m-%d %H:%M:%S')
            result = {}
            for k, v in dict.items():
                if k != 'id' and v:
                    result[k] = {
                        'value': v,
                        'stashed': time_stamp,
                    }
            return json.dumps(result)

        # obtenim els valors a fer stash del model
        ir_model_obj = self.pool.get('ir.model')
        som_stash_setting_obj = self.pool.get("som.stash.setting")

        model_ids = ir_model_obj.search(cursor, uid, [('model', '=', model)])
        if len(model_ids) != 1:
            return

        stash_setting_ids = som_stash_setting_obj.search(
            cursor, uid, [('model', '=', model_ids[0])]
        )
        if not stash_setting_ids:
            return

        # montem diccionari per fer el write i llista per al read
        dict_write = {}
        list_fields_read = []
        som_stash_obj = self.pool.get("som.stash")
        for setting in som_stash_setting_obj.browse(cursor, uid, stash_setting_ids):
            dict_write[setting.field.name] = setting.default_stashed_value
            list_fields_read.append(setting.field.name)

        if not list_fields_read or not dict_write:
            return

        model_obj = self.pool.get(model)
        for id in ids:
            new_dict_data = model_obj.read(cursor, uid, id, list_fields_read)
            value_origin = "{},{}".format(model, str(id))
            stash_id = som_stash_obj.search(cursor, uid, [('origin', '=', value_origin)])
            if len(stash_id) > 0:
                str_data = som_stash_obj.read(cursor, uid, stash_id, ['data'])['data']
                old_dict_data = json.loads(str_data)

                keys_to_update = set(new_dict_data.keys()) - set(old_dict_data.keys())
                for key_to_update in keys_to_update:
                    old_dict_data[key_to_update] = new_dict_data[key_to_update]

                values = {
                    'data': make_stasheable_dict(old_dict_data),
                }
                som_stash_obj.write(cursor, uid, stash_id, values)
            else:
                values = {
                    'origin': value_origin,
                    'data': make_stasheable_dict(new_dict_data),
                }
                som_stash_obj.create(cursor, uid, values)

        # fem el write
        model_obj.write(cursor, uid, ids, dict_write)

    def do_stash_process(self, cursor, uid, ids, context=None):
        msg = _("Resultat d'execució del wizard de backup de dades:\n")
        do_stash = self.read(
            cursor, uid, ids, ['do_stash'], context=context
        )[0]['do_stash']

        partners_to_stash = self.get_partners_origin_to_stash(cursor, uid, context=context)
        msg += _(
            "Trobats {} partners per fer backup.\nLlista d'Ids:\n{}".format(
                len(partners_to_stash),
                ', '.join([str(i) for i in partners_to_stash if i])
            )
        )

        if do_stash:
            self.do_stash_model(cursor, uid, partners_to_stash, 'res.partner')

            list_partners_address_ids = self.get_partners_address(
                cursor, uid, partners_to_stash, context=context
            )
            self.do_stash_model(cursor, uid, list_partners_address_ids, 'res.partner.address')

            list_pol_ids = self.get_polisses(
                cursor, uid, partners_to_stash, context=context
            )
            self.do_stash_model(cursor, uid, list_pol_ids, 'giscedata.polissa')

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
