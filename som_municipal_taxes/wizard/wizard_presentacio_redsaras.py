# -*- coding: utf-8 -*-
from osv import fields, osv
import sys
import logging
import datetime
from dateutil.relativedelta import relativedelta

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("wizard.importador.leads.comercials")


ANUAL_VAL = 5


class WizardPresentacioRedSaras(osv.osv_memory):
    _name = "wizard.presentacio.redsaras"

    def enviar_redsaras(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        if isinstance(ids, list):
            ids = ids[0]

        wizard = self.browse(cursor, uid, ids, context=context)

        # Buscar els municipis que es remesen
        config_obj = self.pool.get('som.municipal.taxes.config')

        search_values = [('red_sara', '=', True), ('active', '=', True)]
        if wizard.quarter == ANUAL_VAL:
            search_values += [('payment', '=', 'year')]
        else:
            search_values += [('payment', '=', 'quarter')]
        if 'from_model' in context:
            search_values += [('id', 'in', context['active_ids'])]

        municipis_conf_ids = config_obj.search(cursor, uid, search_values)

        if not municipis_conf_ids:
            vals = {
                'info': "No hi ha municipis configurats per enviar a Red Saras",
                'state': 'cancel',
            }
            wizard.write(vals, context)
            return True

        context['any'] = wizard.year
        context['trimestre'] = wizard.quarter
        # Encuar per a RedSaras
        municipis_sense_factura = config_obj.encuar_crawlers(
            cursor, uid, ids, municipis_conf_ids, context)
        info = "S'ha encuat la presentació a Red Saras de {}/{} ajuntaments\n\n".format(
            len(municipis_conf_ids) - len(municipis_sense_factura),
            len(municipis_conf_ids)
        )
        if municipis_sense_factura:
            info += "Els següents municipis no s'han enviat perquè no tenen factures:\n"
            info += "\n".join(municipis_sense_factura)

        vals = {
            'info': info,
            'state': 'done',
        }
        wizard.write(vals, context)
        return True

    def show_crawlers_result(self, cursor, uid, ids, context):
        task_id = self.pool.get('ir.model.data').get_object_reference(
            cursor, uid, 'som_crawlers', 'carregar_registre_general',
        )[1]
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        return {
            'domain': "[('task_id','=', {}), ('data_i_hora_execucio', '>', '{}')]".format(
                task_id, today),
            'name': 'Resultat crawlers Registre General',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'som.crawlers.result',
            'type': 'ir.actions.act_window',
        }

    _columns = {
        'state': fields.char('Estat', size=16, required=True),
        "info": fields.text("info"),
        "year": fields.integer("Any", required=True),
        "quarter": fields.selection(
            [(1, '1T'), (2, '2T'), (3, '3T'), (4, '4T'), (ANUAL_VAL, 'Anual')],
            'Trimestre', required=True
        ),
    }

    _defaults = {
        'state': lambda *a: 'init',
        'year': lambda *a: datetime.datetime.today().year,
    }


def get_dates_from_quarter(year, quarter):
    if quarter == ANUAL_VAL:
        return datetime.date(year, 1, 1), datetime.date(year, 12, 31)
    else:
        start_date = datetime.date(year, (quarter - 1) * 3 + 1, day=1)
        return (
            start_date,
            start_date + relativedelta(months=3) - datetime.timedelta(days=1)
        )


WizardPresentacioRedSaras()
