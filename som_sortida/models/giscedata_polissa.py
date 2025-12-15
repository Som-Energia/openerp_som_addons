# -*- coding: utf-8 -*-
from osv import osv, fields
import json
from osv.expression import OOQuery

from datetime import datetime, timedelta
import logging

logger = logging.getLogger('openerp' + __name__)


class GiscedataPolissa(osv.osv):
    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'
    _description = 'Estats d\'una pòlissa en el procés de sortida'

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}

        imd_obj = self.pool.get('ir.model.data')

        _id = super(GiscedataPolissa, self).create(cr, uid, vals, context=context)
        polissa = self.simple_browse(cr, uid, _id)
        state_correcte_id = imd_obj.get_object_reference(
            cr, uid, 'som_sortida', 'enviar_cor_correcte_pending_state'
        )[1]
        state_sense_socia_id = imd_obj.get_object_reference(
            cr, uid, 'som_sortida', 'enviar_cor_contrate_sense_socia_pending_state'
        )[1]
        if not polissa.sortida_state_id:
            if polissa.soci and polissa.soci_nif and not self._es_socia_ct_ss(
                cr, uid, [], polissa.soci_nif, context=context
            ):
                self.write(cr, uid, _id, {"sortida_state_id": state_correcte_id})
            else:
                self.write(cr, uid, _id, {"sortida_state_id": state_sense_socia_id})

        sortida_state_id = self.read(cr, uid, _id, ["sortida_state_id"])["sortida_state_id"][0]
        sense_socia = sortida_state_id == state_sense_socia_id

        if not polissa.sortida_history_ids and sense_socia:
            polissa.sortida_history_ids = [
                (0, 0, {
                    'pending_state_id': state_sense_socia_id,
                    'change_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            ]

        return _id

    def write(self, cr, uid, ids, vals, context=None):  # noqa: C901
        if context is None:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]

        imd_obj = self.pool.get('ir.model.data')
        partner_address_obj = self.pool.get("res.partner.address")
        cat_ss_id = imd_obj.get_object_reference(
            cr, uid, "som_polissa_soci", "origen_ct_sense_socia_category"
        )[1]
        logger = logging.getLogger("openerp.{0}.giscedata_polissa.write".format(__name__))

        if 'soci' in vals:
            soci_obj = self.pool.get('somenergia.soci')
            state_correcte_id = imd_obj.get_object_reference(
                cr, uid, 'som_sortida', 'enviar_cor_correcte_pending_state'
            )[1]
            state_sense_socia_id = imd_obj.get_object_reference(
                cr, uid, 'som_sortida', 'enviar_cor_contrate_sense_socia_pending_state'
            )[1]
            if vals.get('soci', False):
                soci_id = soci_obj.search(cr, uid, [('partner_id', '=', vals.get('soci'))])
                if not soci_id:
                    soci_nif = False
                    logger.info("Log: La socia del contracte no es socia, ojut. Polissa: %s", ids)
                else:
                    soci_id = soci_id[0]
                    soci_nif = soci_obj.read(cr, uid, soci_id, ['vat'], context=context)
                    soci_nif = soci_nif['vat'] if soci_nif else False
            else:
                soci_nif = False

            for _id in ids:
                current_state_id = self.read(cr, uid, _id, ['sortida_state_id'], context=context)[
                    'sortida_state_id']
                if not vals.get('soci', False) or \
                    (vals.get('soci', False) and not soci_nif) or \
                    (soci_nif and not self._es_socia_ct_ss(
                        cr, uid, [_id], soci_nif, context=context)
                     ):
                    if current_state_id != state_correcte_id:
                        vals['sortida_state_id'] = state_correcte_id
                        context['history_pending_state'] = state_correcte_id
                        self.create_history_line(
                            cr, uid, [_id], context=context
                        )
                else:
                    if current_state_id == state_correcte_id:
                        vals['sortida_state_id'] = state_sense_socia_id
                        context['history_pending_state'] = state_sense_socia_id
                        self.create_history_line(
                            cr, uid, [_id], context=context
                        )
                try:
                    category_ids = self.read(cr, uid, _id, ['category_id'])['category_id']
                    if cat_ss_id in category_ids and not self._es_socia_ct_ss(
                            cr, uid, [_id], soci_nif, context=context):
                        partner_address_obj.update_polissa_titular_in_ctss_lists(
                            cr, uid, [_id], context=context,
                        )
                except Exception as e:
                    sentry = self.pool.get('sentry.setup')
                    if sentry:
                        sentry.client.captureException()
                    logger.warning("Error al comunicar amb Mailchimp {}".format(str(e)))

        res = super(GiscedataPolissa, self).write(cr, uid, ids, vals, context=context)

        """Si s'afegeix la categoria origen_ct_sense_socia_category a la pòlissa,
        subscribim a llista mailchimp_clients_ctss_list al titular de la pòlissa."""
        if "category_id" in vals:
            # Comprovar si s'està afegint la categoria cat_ss_id
            # Les operacions (4, id) i (6, 0, [ids]) afegeixen categories
            is_adding_cat_ss = False
            for operation in vals["category_id"]:
                if operation[0] == 4 and operation[1] == cat_ss_id:
                    # Operació (4, id): afegir relació
                    is_adding_cat_ss = True
                    break
                elif operation[0] == 6 and cat_ss_id in operation[2]:
                    # Operació (6, 0, [ids]): reemplaçar amb llista d'ids
                    is_adding_cat_ss = True
                    break

            if is_adding_cat_ss:
                try:
                    for polissa in self.browse(cr, uid, ids, context=context):
                        partner_address_obj.subscribe_polissa_titular_in_ctss_lists(
                            cr, uid, [polissa.id], context=context,
                        )
                except Exception as e:
                    sentry = self.pool.get('sentry.setup')
                    if sentry:
                        sentry.client.captureException()
                    logger.warning("Error al comunicar amb Mailchimp {}".format(str(e)))
        return res

    def _es_socia_ct_ss(self, cr, uid, ids, socia_nif, context=None):
        """
        Check if the polissa is linked to a ct ss socia.
        :param socia_nif: NIF of the socia
        :return: True if the socia is in the ct ss, False otherwise
        """
        config_obj = self.pool.get('res.config')
        nifs_ct_ss = config_obj.get(cr, uid, 'llista_nifs_socia_ct_ss', '[]')
        nifs_ct_ss = json.loads(nifs_ct_ss)
        return socia_nif in nifs_ct_ss

    def _get_te_socia_real_vinculada(self, cr, uid, ids, field_name, arg, context=None):
        """Get the default value for 'te_socia_real_vinculada'."""
        res = dict.fromkeys(ids, True)
        pol_data = self.read(cr, uid, ids, ['soci', 'soci_nif'], context=context)

        for pol in pol_data:
            if self._es_socia_ct_ss(cr, uid, ids, pol.get('soci_nif')):
                res[pol['id']] = False
        return res

    def _get_en_process_de_sortida(self, cr, uid, ids, field_name, arg, context=None):
        """Check if the polissa is in process of sortida."""
        res = dict.fromkeys(ids, False)
        for polissa in self.browse(cr, uid, ids, context=context):
            if polissa.sortida_state_id \
                    and polissa.sortida_state_id.weight > 0 \
                    and polissa.sortida_state_id.weight < 70:
                res[polissa.id] = True
            else:
                res[polissa.id] = False
        return res

    def _get_cor_submission_date(self, cr, uid, ids, field_name, arg, context=None):
        """Date when the polissa is going to be sent to the COR."""
        imd_obj = self.pool.get('ir.model.data')
        correcte_state_id = imd_obj.get_object_reference(
            cr, uid, 'som_sortida', 'enviar_cor_correcte_pending_state')[1]
        state_id_to_days = {
            imd_obj.get_object_reference(
                cr, uid, 'som_sortida', 'enviar_cor_contrate_sense_socia_pending_state')[1]: 365,
            imd_obj.get_object_reference(
                cr, uid, 'som_sortida', 'enviar_cor_pendent_falta_un_mes_pending_state')[1]: 30,
            imd_obj.get_object_reference(
                cr, uid, 'som_sortida', 'enviar_cor_falta_un_mes_pending_state')[1]: 30,
            imd_obj.get_object_reference(
                cr, uid, 'som_sortida', 'enviar_cor_pendent_falta_15_dies_pending_state')[1]: 15,
            imd_obj.get_object_reference(
                cr, uid, 'som_sortida', 'enviar_cor_falta_15_dies_pending_state')[1]: 15,
            imd_obj.get_object_reference(
                cr, uid, 'som_sortida', 'enviar_cor_pendent_falta_7_dies_pending_state')[1]: 7,
            imd_obj.get_object_reference(
                cr, uid, 'som_sortida', 'enviar_cor_falta_7_dies_pending_state')[1]: 7,
        }
        res = dict.fromkeys(ids, False)
        current_pending_state_info = self.get_current_pending_state_info(
            cr, uid, ids, context=context)
        for polissa in self.browse(cr, uid, ids, context=context):
            if not polissa.sortida_state_id or polissa.sortida_state_id.id == correcte_state_id:
                continue
            state_initial_date = datetime.strptime(
                current_pending_state_info[polissa.id]['change_date'], "%Y-%m-%d")
            # If not in state_id_to_days, is in process to be sent so just return the initial date
            days_to_add = state_id_to_days.get(polissa.sortida_state_id.id, 0)
            res[polissa.id] = (state_initial_date + timedelta(days=days_to_add))
        return res

    _STORE_SOCIA_VINCULADA = {
        'giscedata.polissa': (lambda self, cr, uid, ids, c={}: ids, ['soci_nif', 'soci'], 20),
    }

    _STORE_PROCESS_DE_SORTIDA = {
        'giscedata.polissa': (lambda self, cr, uid, ids, c={}: ids, ['sortida_state_id'], 20),
    }

    _columns = {
        'sortida_state_id': fields.many2one(
            'som.sortida.state',
            'Estat de sortida',
            help='Estat de la pòlissa sense sòcia en el procés de sortida a la COR',
        ),
        'sortida_history_ids': fields.one2many(
            'som.sortida.history',
            'polissa_id',
            'Historial de sortides',
            help='Historial de sortides relacionades amb aquesta pòlissa',
        ),
        'te_socia_real_vinculada': fields.function(
            _get_te_socia_real_vinculada, method=True, string='Sòcia real vinculada',
            type="boolean", store=_STORE_SOCIA_VINCULADA,
            help="Indica si la pòlissa té sòcia real vinculada o és de la campanya CT SS",
        ),
        'en_process_de_sortida': fields.function(
            _get_en_process_de_sortida, method=True, string='En procés de sortida',
            type="boolean", store=_STORE_PROCESS_DE_SORTIDA,
            help="Indica si la pòlissa està en procés de sortida",
        ),
        'cor_submission_date': fields.function(
            _get_cor_submission_date, method=True, string='Data enviament a la COR',
            type="date"
        ),
    }

    def go_on_pending(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]
        if not ids:
            return False
        pstate_obj = self.pool.get('som.sortida.state')
        only_active = context.get('only_active', True)
        q = OOQuery(self, cursor, uid)
        sql = q.select([
            'id', 'sortida_state_id.weight',
            'sortida_state_id.process_id', 'sortida_state_id.active',
        ], only_active=only_active).where([('id', 'in', ids)])
        cursor.execute(*sql)
        res = cursor.dictfetchall()
        for pol in res:
            weight = pol['sortida_state_id.weight']
            process_id = pol['sortida_state_id.process_id']
            active = pol['sortida_state_id.active']
            ctx = context.copy()
            if not active:
                ctx.update({'current_state_deactivated': True})
            pstate_id = pstate_obj.get_next(cursor, uid, weight, process_id, context=ctx)
            self.set_pending(cursor, uid, [pol['id']], pstate_id)
        return True

    def set_pending(self, cursor, uid, ids, pending_id, context=None):
        """ A history line will be created and the pending_state field will
        be changed with the last history line pending_state value."""
        if context is None:
            context = {}
        context.update({'history_pending_state': pending_id})
        self.write(cursor, uid, ids, {'sortida_state_id': pending_id}, context=context)
        res = self.create_history_line(cursor, uid, ids, context)
        return res

    def create_history_line(self, cursor, uid, ids, context=None):
        """
        :param cursor: database cursor
        :param uid: user identifier
        :param ids: ids of the polissas changed
        :param context: dictionary with the context which must
                        include the pending_stat id
        :return: Returns True if some record has been created
        """
        if context is None:
            context = {}

        # Custom change date format
        # Careful ids should be account_polissa todo convert on facturacio.set_pending?
        # [(polissa_id, 'YYYY-MM-DD %H:%M:%S'), (polissa_id_2, 'YYYY-MM-DD)]
        custom_change_dates = dict(context.get('custom_change_dates', []) or [])

        if not isinstance(ids, list):
            ids = [ids]
        pending_history_obj = self.pool.get('som.sortida.history')
        imd_obj = self.pool.get('ir.model.data')
        process_id = imd_obj.get_object_reference(
            cursor, uid, 'som_sortida', 'enviar_cor_state_process')[1]
        next_state = context.get(
            'history_pending_state', self._get_default_pending(cursor, uid, process_id=process_id)
        )
        registers_created = 0
        last_lines = self.get_current_pending_state_info(cursor, uid, ids)
        for current_pol_id in ids:
            default_change_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            change_date = default_change_date
            custom_change_d = custom_change_dates.get(current_pol_id, False)
            if (
                custom_change_d and (
                    not last_lines[current_pol_id]
                    or custom_change_d >= last_lines[current_pol_id]['change_date']
                )
            ):
                change_date = custom_change_d
            if last_lines[current_pol_id]:
                pending_history_obj.write(
                    cursor, uid, last_lines[current_pol_id]['id'], {
                        'end_date': change_date
                    }
                )
            res = pending_history_obj.create(cursor, uid, {
                'pending_state_id': next_state,
                'change_date': change_date,
                'polissa_id': current_pol_id
            })
            if res:
                registers_created += 1
        return registers_created > 0

    def _get_default_pending(self, cursor, uid, process_id=None, context=None):
        """Get the default pending state for a polissa."""
        imd_obj = self.pool.get('ir.model.data')
        state_id = imd_obj.get_object_reference(
            cursor, uid, 'som_sortida', 'enviar_cor_state_process'
        )[1]
        return state_id

    def get_current_pending_state_info(self, cursor, uid, ids, context=None):
        """
            Get the info of the last history line by polissa id.
        :return: a dict containing the info of the last history line of the
                 polissa indexed by its id.
                 ==== Fields of the dict for each polissa ===
                 'id': if of the last account.polissa.pending.history
                 'pending_state_id': id of its pending_state
                 'change_date': date of change (also, date of the creation of
                                the line)
        """
        if context is None:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]
        pending_history_obj = self.pool.get('som.sortida.history')
        result = dict.fromkeys(ids, False)
        fields_to_read = ['pending_state_id', 'change_date', 'polissa_id']
        for id in ids:
            res = pending_history_obj.search(
                cursor, uid, [('polissa_id', '=', id)]
            )
            if res:
                # We consider the last record the first one due to order
                # statement in the model definition.
                values = pending_history_obj.read(
                    cursor, uid, res[0], fields_to_read)
                result[id] = {
                    'id': values['id'],
                    'pending_state_id': values['pending_state_id'][0],
                    'change_date': values['change_date'],
                }
            else:
                result[id] = False
        return result

    def request_submission_to_cor(self, cursor, uid, pol_id, context=None):
        """
        Request the submission of the polissa to the COR.
        :param pol_id: id of the polissa to submit
        :return: ATR case ID
        """
        if context is None:
            context = {}

        polissa_obj = self.pool.get("giscedata.polissa")
        polissa = polissa_obj.browse(cursor, uid, pol_id, context=context)
        self._check_submittable_to_cor(cursor, uid, polissa, context=context)

        ctx = context.copy()
        ctx.update({"sector": "energia"})
        data_accio = datetime.today()

        config = dict(
            data_accio=data_accio.strftime("%Y-%m-%d"),
            motiu="02",
            activacio="A",
            phone_pre="0034",  # FIXME: Use new ERP prefixes when available
            phone_num=polissa.titular.address[0].phone,
        )
        res = polissa_obj.crear_cas_atr(cursor, uid, pol_id, "B1", config, context=ctx)

        sw_id = res[2]
        if not sw_id:
            raise osv.except_osv(
                "Error!", "Polissa {}: {}".format(polissa.name, res[1])
            )

        return sw_id

    def _check_submittable_to_cor(self, cursor, uid, polissa, context=None):
        if context is None:
            context = {}
        sw_obj = self.pool.get("giscedata.switching")
        pstate_obj = self.pool.get('account.invoice.pending.state')
        imd_obj = self.pool.get('ir.model.data')

        correct_state_id = imd_obj.get_object_reference(
            cursor, uid, 'account_invoice_pending',
            'default_invoice_pending_state'
        )[1]
        correct = pstate_obj.read(cursor, uid, correct_state_id, ['name'])['name']

        has_open_atr_cases = bool(sw_obj.search(
            cursor, uid, [
                ("cups_polissa_id", "=", polissa.id),
                ("state", "in", ["draft", "open", "pending"]),
            ]
        ))

        if (
            polissa.te_socia_real_vinculada
            or not polissa.state == 'activa'
            or polissa.pending_state != correct
            or has_open_atr_cases
        ):
            raise osv.except_osv(
                "Error!", "La polissa {} no és enviable a la COR".format(polissa.name)
            )


GiscedataPolissa()
