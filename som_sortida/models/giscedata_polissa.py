# -*- coding: utf-8 -*-
from osv import osv, fields
import json
from osv.expression import OOQuery
from datetime import datetime


class GiscedataPolissa(osv.osv):
    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'
    _description = 'Estats d\'una pòlissa en el procés de sortida'

    def create(self, cr, uid, vals, context=None):
        _id = super(GiscedataPolissa, self).create(cr, uid, vals, context=context)
        vals = self.browse(cr, uid, _id)
        if not vals.sortida_state_id:
            imd_obj = self.pool.get('ir.model.data')
            state_correcte_id = imd_obj.get_object_reference(
                cr, uid, 'som_sortida', 'enviar_cor_correcte_pending_state'
            )[1]
            state_sense_socia_id = imd_obj.get_object_reference(
                cr, uid, 'som_sortida', 'enviar_cor_contrate_sense_socia_pending_state'
            )[1]
            if vals.soci and vals.soci_nif and not self._es_socia_promocional(
                cr, uid, [], vals.soci_nif, context=context
            ):
                vals.sortida_state_id = state_correcte_id
            else:
                vals.sortida_state_id = state_sense_socia_id

        if not vals.sortida_history_ids and vals.sortida_state_id == state_sense_socia_id:
            vals.sortida_history_ids = [
                (0, 0, {
                    'pending_state_id': state_sense_socia_id,
                    'change_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            ]

        return _id

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]

        if 'soci' in vals:
            imd_obj = self.pool.get('ir.model.data')
            state_correcte_id = imd_obj.get_object_reference(
                cr, uid, 'som_sortida', 'enviar_cor_correcte_pending_state'
            )[1]
            state_sense_socia_id = imd_obj.get_object_reference(
                cr, uid, 'som_sortida', 'enviar_cor_contrate_sense_socia_pending_state'
            )[1]
            for _id in ids:
                if vals.get('soci', False) and vals.get('soci_nif') and \
                    not self._es_socia_promocional(
                        cr, uid, [_id], vals['soci_nif'], context=context
                ):
                    vals['sortida_state_id'] = state_correcte_id
                else:
                    vals['sortida_state_id'] = state_sense_socia_id
                change_date = context.get('change_date', False) or \
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                vals['sortida_history_ids'] = [
                    (0, 0, {
                        'pending_state_id': state_sense_socia_id,
                        'change_date': change_date,
                        'polissa_id': _id,
                    })
                ]
        return super(GiscedataPolissa, self).write(cr, uid, ids, vals, context=context)

    def _es_socia_promocional(self, cr, uid, ids, socia_nif, context=None):
        """
        Check if the polissa is linked to a promotional socia.
        :param socia_nif: NIF of the socia
        :return: True if the socia is promotional, False otherwise
        """
        config_obj = self.pool.get('res.config')
        nifs_promocionals = config_obj.get(cr, uid, 'llista_nifs_socia_promocional', '[]')
        nifs_promocionals = json.loads(nifs_promocionals)
        return socia_nif in nifs_promocionals

    def _get_initial_sortida_state(self, cr, uid, context=None):
        """Get the initial state for a new sortida."""
        imd_obj = self.pool.get('ir.model.data')
        state_id = imd_obj.get_object_reference(
            cr, uid, 'som_sortida', 'enviar_cor_correcte_pending_state'
        )[1]

        if state_id:
            return state_id
        else:
            return False

    def _get_socia_real_vinculada(self, cr, uid, ids, field_name, arg, context=None):
        """Get the default value for 'te_socia_real_vinculada'."""
        res = dict.fromkeys(ids, True)
        config_obj = self.pool.get('res.config')
        nifs_promocionals = config_obj.get(cr, uid, 'llista_nifs_socia_promocional', '[]')
        nifs_promocionals = json.loads(nifs_promocionals)
        pol_data = self.read(cr, uid, ids, ['soci', 'soci_nif'], context=context)

        for pol in pol_data:
            if not pol['soci'] or not pol['soci_nif']:
                res[pol['id']] = False
            elif self._es_socia_promocional(cr, uid, ids, pol['soci_nif']):
                res[pol['id']] = False
            else:
                res[pol['id']] = True
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
            _get_socia_real_vinculada, method=True, string='Sòcia real vinculada',
            type="boolean", store=_STORE_SOCIA_VINCULADA,
            help="Indica si la pòlissa té sòcia real vinculada o és promocional",
        ),
        'en_process_de_sortida': fields.function(
            _get_en_process_de_sortida, method=True, string='En procés de sortida',
            type="boolean", store=_STORE_PROCESS_DE_SORTIDA,
            help="Indica si la pòlissa està en procés de sortida",
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
            if custom_change_d and custom_change_d >= last_lines[current_pol_id]['change_date']:
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


GiscedataPolissa()
