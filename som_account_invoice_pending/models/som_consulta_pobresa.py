# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import datetime, timedelta

RESOLUTION_STATES = [
    ('positiva', 'Positiva'),
    ('negaviva', 'Negativa'),
]


class SomConsultaPobresa(osv.osv):
    _name = 'som.consulta.pobresa'
    _inherits = {"crm.case": "crm_id"}
    _description = 'Model per gestionar les consultes de pobresa energètica'

    def case_close_pobresa(self, cr, uid, ids, *args):
        crm_obj = self.pool.get('crm.case')
        consultes = self.browse(cr, uid, ids)
        for consulta in consultes:
            if not consulta.resolucio:
                raise osv.except_osv(
                    "Falta resolució",
                    "Per poder tancar la consulta s'ha d'informar el camp resolució.")
        args[0]['origin'] = self._name
        crm_ids = [consulta.crm_id.id for consulta in consultes]
        response = crm_obj.case_close(cr, uid, crm_ids, *args)

        consultes = self.browse(cr, uid, ids)
        for consulta in consultes:
            if consulta.state == 'done' and consulta.resolucio == 'positiva':
                self.moure_factures_pobresa(cr, uid, consulta)

        return response

    def case_open_pobresa(self, cr, uid, ids, *args):
        crm_obj = self.pool.get('crm.case')
        consultes = self.browse(cr, uid, ids)
        crm_ids = [consulta.crm_id.id for consulta in consultes]
        response = crm_obj.case_open(cr, uid, crm_ids, *args)
        return response

    def case_pending_pobresa(self, cr, uid, ids, *args):
        crm_obj = self.pool.get('crm.case')
        consultes = self.browse(cr, uid, ids)
        crm_ids = [consulta.crm_id.id for consulta in consultes]
        response = crm_obj.case_pending(cr, uid, crm_ids, *args)
        return response

    def case_log_pobresa(self, cr, uid, ids, *args):
        crm_obj = self.pool.get('crm.case')
        consultes = self.browse(cr, uid, ids)
        crm_ids = [consulta.crm_id.id for consulta in consultes]
        response = crm_obj.case_log(cr, uid, crm_ids, *args)
        return response

    def autoassign_pobresa(self, cr, uid, ids, *args):
        crm_obj = self.pool.get('crm.case')
        consultes = self.browse(cr, uid, ids)
        crm_ids = [consulta.crm_id.id for consulta in consultes]
        response = crm_obj.autoassign(cr, uid, crm_ids, *args)
        return response

    def moure_factures_pobresa(self, cr, uid, cas):
        gff_obj = self.pool.get('giscedata.facturacio.factura')
        imd_obj = self.pool.get("ir.model.data")
        pobresa_state_id = imd_obj.get_object_reference(
            cr, uid, "som_account_invoice_pending", "probresa_energetica_certificada_pending_state"
        )[1]
        search_params = [
            ('partner_id', '=', cas.partner_id.id),
            ('polissa_id', '=', cas.polissa_id.id),
        ]
        gff_ids = gff_obj.search(cr, uid, search_params)
        gffs = gff_obj.browse(cr, uid, gff_ids)
        for gff in gffs:
            if gff.pending_state.weight > 0:
                gff_obj.set_pending(cr, uid, [gff.id], pobresa_state_id)

    def consulta_pobresa_activa(self, cr, uid, ids, partner_id, polissa_id, context=None):
        cfg_obj = self.pool.get('res.config')
        ndays = int(cfg_obj.get(cr, uid, 'password_policy', '335'))
        start_day_valid = (datetime.today()
                           - timedelta(days=ndays)).strftime('%Y-%m-%d')

        search_params = [
            ('partner_id', '=', partner_id),
            ('polissa_id', '=', polissa_id),
        ]
        scp_list = self.search(cr, uid, search_params, context)
        scps = self.browse(cr, uid, scp_list, context)

        for scp in scps:
            if (scp.state == 'done' and scp.date_closed > start_day_valid) or (
                    scp.state == 'pending' and scp.date > start_day_valid):
                return scp
        return False

    def _ff_get_titular(self, cr, uid, ids, field, arg, context=None):
        """ Anem a buscar el titular de la pólissa assignada (si en té) """
        res = {}
        if not context:
            context = {}
        scp_obj = self.pool.get('som.consulta.pobresa')
        consultes = scp_obj.browse(cr, uid, ids)
        for c in consultes:
            res[c.id] = (c.polissa_id and c.polissa_id.titular.name
                         or False)
        return res

    def _ff_get_nif_titular(self, cr, uid, ids, field, arg, context=None):
        """ Anem a buscar el titular de la pólissa assignada (si en té) """
        res = {}
        if not context:
            context = {}
        scp_obj = self.pool.get('som.consulta.pobresa')
        consultes = scp_obj.browse(cr, uid, ids)
        for c in consultes:
            res[c.id] = (c.polissa_id and c.polissa_id.titular_nif
                         or False)
        return res

    def _ff_get_municipi(self, cr, uid, ids, field, arg, context=None):
        """ Anem a buscar el municipi del cups de la pólissa assignada (si en té) """
        res = {}
        if not context:
            context = {}
        scp_obj = self.pool.get('som.consulta.pobresa')
        consultes = scp_obj.browse(cr, uid, ids)
        for c in consultes:
            res[c.id] = (c.polissa_id and c.polissa_id.cups.id_municipi.name
                         or False)
        return res

    def _ff_get_direccio_cups(self, cr, uid, ids, field, arg, context=None):
        """ Anem a buscar el municipi del cups de la pólissa assignada (si en té) """
        res = {}
        if not context:
            context = {}
        scp_obj = self.pool.get('som.consulta.pobresa')
        consultes = scp_obj.browse(cr, uid, ids)
        for c in consultes:
            res[c.id] = (c.polissa_id and c.polissa_id.cups.direccio
                         or False)
        return res

    def _ff_get_email_titular(self, cr, uid, ids, field, arg, context=None):
        """ Anem a buscar el titular de la pólissa assignada (si en té) """
        res = {}
        if not context:
            context = {}
        scp_obj = self.pool.get('som.consulta.pobresa')
        consultes = scp_obj.browse(cr, uid, ids)
        for c in consultes:
            res[c.id] = (c.polissa_id and c.polissa_id.direccio_notificacio.email
                         or False)
        return res

    _columns = {
        'crm_id': fields.many2one('crm.case', required=True),
        'titular_id': fields.function(
            _ff_get_titular, method=True,
            string='Titular', type='char', size=128, store=True),
        'municipi': fields.function(
            _ff_get_municipi, method=True,
            string="Municipi", type='char', size=128, store=True),
        'numero_registre': fields.char("Número de registre", size=128),
        'agrupacio_supramunicipal': fields.many2one('agrupacio.supramunicipal',
                                                    'Agrupació supramunicipal'),
        'direccio_cups': fields.function(
            _ff_get_direccio_cups, method=True,
            string="Direcció CUPS", type='char', size=128, store=True),
        'email_partner': fields.function(
            _ff_get_email_titular, method=True,
            string="Email titular", type='char', size=128, store=True),
        'resolucio': fields.selection(RESOLUTION_STATES, 'Resolució', size=16),
        'nif_titular': fields.function(
            _ff_get_nif_titular, method=True,
            string='NIF Titular', type='char', size=128, store=True),
    }

    _defaults = {
        'section_id': lambda obj, cr, uid, context: obj.pool.get('crm.case.section').search(cr, uid, [('code', '=', 'BSCPE')])[0],  # noqa: E501
    }

    _order = "id desc"


SomConsultaPobresa()
