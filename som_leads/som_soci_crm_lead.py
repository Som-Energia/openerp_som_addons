# -*- coding: utf-8 -*-
from __future__ import absolute_import
from osv import osv, fields
from tools.translate import _
from base_iban.base_iban import _format_iban
from base.res.partner.partner import _lang_get
from tools.misc import cache
from service.security import Sudo

class SomSociCrmLead(osv.OsvInherits):

    _name = "som.soci.crm.lead"
    _inherits = {"crm.case": "crm_id"}
    _order = "id desc"
    _description = _(u"Somenergia Soci CRM Leads")


    lead_partner_adr_to_adr = {
        'address_zip': 'zip',
        'address_municipi_id': 'id_municipi',
        'address_poblacio_id': 'id_poblacio',
        'address_nv': 'nv',
        'address_email': 'email',
        'address_phone': 'phone',
        'address_mobile': 'mobile',
        # 'titular_pnp': 'pnp',
        # 'titular_bq': 'bq',
        # 'titular_es': 'es',
        # 'titular_pt': 'pt',
        # 'titular_pu': 'pu',
        # 'titular_cpo': 'cpo',
        # 'titular_cpa': 'cpa',
        # 'titular_tv': 'tv',
    }

    def unlink(self, cursor, uid, ids, context=None):
        """
        Com que hi ha el ondelete cascade, quan s'elimina un CRM s'elimina el CRM LEAD, pero quan se'limina un
        CRM LEAD no se'limina el CRM.
        El que fem es cridar directament el unlink de CRM amb els ids del CRM i aixi s'elimina tot.
        """
        if not context:
            context = {}
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        crm_obj = self.pool.get('crm.case')
        crm_ids = [
            crm_tala_data['crm_id'][0]
            for crm_tala_data in self.read(cursor, uid, ids, ['crm_id'])
        ]
        return crm_obj.unlink(cursor, uid, crm_ids, context=context)

    def create(self, cursor, uid, vals, context=None):
        if vals is None:
            vals = {}
        new_vals = self._clean_and_fill_values(cursor, uid, vals, context=context)

        for camp, valor in new_vals.items():
            if camp not in vals:
                vals[camp] = valor

        res_id = super(osv.osv, self).create(cursor, uid, vals, context)
        lead_v = self.read(cursor, uid, res_id, ['stage_id'], context=context)
        if not lead_v['stage_id']:
            self.stage_next(cursor, uid, [res_id], context=context)

        return res_id

    def write(self, cursor, uid, ids, vals, context=None):
        if context is None:
            context = {}
        if vals is None:
            vals = {}

        self._clean_values(cursor, uid, vals, context=context)

        res = super(osv.osv, self).write(cursor, uid, ids, vals, context)

        return res

    #TODO: ajustar als camps que tenim
    def _clean_and_fill_values(self, cursor, uid, values, context=None):
        if context is None:
            context = {}
        sobreescriure_sempre = ['titular_vat', 'cups', 'iban', 'distribuidora_vat'
                                ] + context.get("sobreescriure_sempre_extra", [])
        new_vals = {}
        # Camps del titular
        if values.get("titular_vat"):
            new_vals.update(self._get_values_titular(cursor, uid, values.get("titular_vat"), context=context))

        # Camps del IBAN
        if values.get("iban") or new_vals.get("titular_vat"):
            new_vals.update(self._get_values_iban(cursor, uid, values.get("iban"), titular_vat=new_vals.get("titular_vat"), context=context))

        # Autocompletar els municipis desde les poblacions
        if values.get("titular_id_municipi") or new_vals.get("titular_id_poblacio"):
            new_vals.update(self._get_values_poblacio_municipi(cursor, uid, prefix="titular_", municipi_id=values.get("titular_id_municipi"), poblacio_id=new_vals.get("titular_id_poblacio"), context=context))

        values_cpy = values.copy()
        # Emplenem nomes els camps que no tinguem ja
        for key, val in new_vals.iteritems():
            if key not in values or not values.get(key) or key in sobreescriure_sempre:
                if val is None:
                    val = False
                values_cpy[key] = val

        res_vals = self._clean_values(cursor, uid, values_cpy, context=None)
        return res_vals

    #TODO: ajustar als camps que tenim
    def _clean_values(self, cursor, uid, values, context=None):
        values_cpy = values.copy()
        # Netejem els camps char en general per treure espais al final
        fields_to_strip = [c[0] for c in self._columns.iteritems() if c[0] in values and c[1]._type == "char"]
        for to_strip in fields_to_strip:
            if values_cpy[to_strip]:
                values_cpy[to_strip] = values_cpy[to_strip].strip()
        # Convertimos todos los valores de None a False para que no dé
        # conflictos con el XML-RPC
        values_coalesced = {
            k: False if v is None else v for (k, v) in values_cpy.items()
        }
        return values_coalesced
    """
    def _get_values_titular(self, cursor, uid, vat, context=None):
        vals = {'titular_vat': vat}
        if not vat:
            return vals

        part_o = self.pool.get("res.partner")

        # Posem el "ES" al davant
        if len(vals.get("titular_vat")) <= 9:
            vals['titular_vat'] = "ES" + vals['titular_vat']
        vals['titular_vat'] = vals['titular_vat'].upper()

        # Comprovem si es una empresa
        vals['titular_es_empresa'] = part_o.is_enterprise_vat(vals['titular_vat'])

        return vals

    def _get_values_iban(self, cursor, uid, iban, titular_vat=None, context=None):
        return {'iban': _format_iban(iban)}

    def _get_values_poblacio_municipi(self, cursor, uid, prefix="titular_", municipi_id=None, poblacio_id=None, context=None):
        vals = {
            prefix+'id_municipi': municipi_id,
            prefix+'id_poblacio': poblacio_id,
        }
        if not municipi_id and not poblacio_id:
            return vals
        poblacio_o = self.pool.get("res.poblacio")

        # Completem el municipi a partir de la poblacio
        if poblacio_id and not municipi_id:
            mid = poblacio_o.read(cursor, uid, poblacio_id, ['municipi_id'])['municipi_id']
            vals[prefix+'id_municipi'] = mid and mid[0] or False

        # Completem la poblacio a aprtir del municipi
        if not poblacio_id and municipi_id:
            pids = poblacio_o.search(cursor, uid, [('municipi_id', '=', municipi_id)])
            if len(pids) == 1:
                vals[prefix + 'id_poblacio'] = pids[0]
            else:
                vals[prefix + 'id_poblacio'] = False

        return vals
    """

    def onchange_generic(self, cr, uid, ids, *args):
        res = {}
        vals = {}
        i = 0
        while i < len(args):
            calu = args[i]
            valor = args[i+1]
            vals[calu] = valor
            i += 2
        new_vals = self._clean_and_fill_values(cr, uid, vals)
        res['value'] = new_vals

        return res


    def run_method(self, cr, uid, id, context):
        if isinstance(id, (tuple, list)):
            id = id[0]

        stage = self.browse(cr, uid, id).stage_id
        if stage:
            stage = stage.id
            stage_obj = self.pool.get('crm.case.stage')
            method = stage_obj.read(cr, uid, stage, ['method'])['method']
            if method:
                func = getattr(self, method)
                result = func(cr, uid, [id], context)


    def stage_next(self, cr, uid, ids, context=None):
        crm_obj = self.pool.get('crm.case')
        for _id in ids:
            self.run_method(cr, uid, _id, context)
            crm_id = self.read(cr, uid, _id, ['crm_id'])['crm_id'][0]
            res = crm_obj.stage_next(cr, uid, [crm_id], context)

        return res

    def _vat_es_empresa(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = {}
        partner_o = self.pool.get("res.partner")
        for inf in self.read(cr, uid, ids, ['partner_vat']):
            vat = inf['partner_vat']
            res[inf['id']] = partner_o.is_enterprise_vat(vat) if vat else False
        return res

    def create_entity_partner(self, cursor, uid, crml_id, context=None):
        if context is None:
            context = {}
        if isinstance(crml_id, (list, tuple)):
            crml_id = crml_id[0]

        partner_o = self.pool.get("res.partner")
        adr_o = self.pool.get("res.partner.address")
        municipi_o = self.pool.get("res.municipi")

        adr_partner_fields = self.lead_partner_adr_to_adr.keys()
        opt_fields = adr_partner_fields[:]
        opt_fields.extend(['partner_lang'])
        mandatory_fields = ['partner_vat', 'partner_nom']

        info = self._check_and_get_mandatory_fields(cursor, uid, crml_id, mandatory_fields, opt_fields, context=context)


        aid = None
        tids = partner_o.search(cursor, uid, [('vat', '=', info['partner_vat'])])
        if len(tids):
            tid = tids[0]
            res = _(u"Se ha encontrado un titular con numero de documento {0}, no se creara una nueva ficha de empresa. ").format(info['partner_vat'])
            # Comprovem si l'adreça tamb existeix
            sp = [('partner_id', '=', tid)]
            for f, val in info.iteritems():
                if f not in self.lead_partner_adr_to_adr.keys():
                    continue
                if isinstance(val, (list, tuple)):
                    val = val[0]
                sp.append((self.lead_partner_adr_to_adr.get(f), '=', val))
            adrids = adr_o.search(cursor, uid, sp)
            if len(adrids):
                aid = adrids[0]
                res += _(u"La direccion del titular encontrado coincide con la actual, no se creara una nueva direccion.")
                crear_address = False
            else:
                crear_address = True
        else:
            crear_address = True

            create_vals = {
                'name': info['partner_nom'],
                'vat': info['partner_vat'],
                'lang': info['partner_lang']
            }
            tid = partner_o.create(cursor, uid, create_vals)
            res = _(u"Se ha creado un nuevo titular con numero de documento {0}. ").format(info['partner_vat'])

        if tid:
            self.write(cursor, uid, [crml_id], {'partner_id': tid}, context=context)

        if crear_address:
            create_vals = {'name': info['partner_nom'], 'partner_id': tid}
            for fname, fval in info.iteritems():
                if not fval:
                    continue
                if isinstance(fval, (list, tuple)):
                    fval = fval[0]
                if fname in ['titular_nom', 'titular_cognom1', 'titular_cognom2']:
                    continue
                create_vals[self.lead_partner_adr_to_adr.get(fname, fname)] = fval
            if create_vals.get("id_municipi") and not create_vals.get("state_id"):
                create_vals["state_id"] = municipi_o.read(cursor, uid, create_vals.get("id_municipi"), ['state'])['state'][0]
            aid = adr_o.create(cursor, uid, create_vals)
            res += _(u"Ninguna direccion del titular coincide con la actual, se ha creado una nueva direccion.")

        if aid:
            self.write(cursor, uid, [crml_id], {'partner_address_id': aid}, context=context)

        return res

    def create_entity_soci(self, cursor, uid, crml_id, context=None):
        if context is None:
            context = {}
        if isinstance(crml_id, (list, tuple)):
            crml_id = crml_id[0]

        soci_o = self.pool.get("somenergia.soci")
        partner_id = self.read(cursor, uid, crml_id, ['partner_id'])['partner_id'][0]
        soci_id = soci_o.search(cursor, uid, [('partner_id', '=', partner_id), ('baixa','=', False)], context=context)
        res = ''
        if soci_id:
            raise _("Ja existeix el soci i està actiu")
            res = _(
                u"S'ha trobat un soci amb el partner_id {}. No es crea un nou soci i s'activa l'existent"
            ).format(partner_id)
        else:
            soci_id = soci_o.create_one_soci(cursor, uid, partner_id, context)
            res = _(u"S'ha creat o activat el soci")
        if isinstance(soci_id, (list, tuple)):
            soci_id = soci_id[0]
        self.write(cursor, uid, [crml_id], {'soci_id': soci_id}, context=context)

        return res

    def create_mandatory_apo(self, cursor, uid, crml_id, context=None):
        if context is None:
            context = {}
        if isinstance(crml_id, (list, tuple)):
            crml_id = crml_id[0]
        conf_o = self.pool.get('res.config')
        investment_o = self.pool.get("generationkwh.investment")
        emission_o = self.pool.get("generationkwh.emission")

        quota_amount = eval(conf_o.get(cursor, uid, 'quota_soci_amount', '100'))

        li = self.read(cursor, uid, crml_id, ['partner_id', 'ip', 'iban', 'partner_date'])

        investment_id = investment_o.create_from_form(
            cursor, uid, li['partner_id'][0], li['partner_date'], quota_amount, li['ip'],
            str(li['iban']), 'APO_OB', context
        )
        self.write(cursor, uid, [crml_id], {'investment_id': investment_id}, context=context)
        return 'TODO'

    #TODO: potser no cal pq ho fa el create_from_form?
    def create_entity_iban(self, cursor, uid, crml_id, context=None):
        if context is None:
            context = {}
        if isinstance(crml_id, (list, tuple)):
            crml_id = crml_id[0]

        partner_o = self.pool.get("res.partner")
        addr_o = self.pool.get("res.partner.address")
        bank_o = self.pool.get("res.partner.bank")
        payment_mode_o = self.pool.get("payment.mode")
        res_country = self.pool.get('res.country')

        lead = self.read(cursor, uid, crml_id, ['iban_other_owner'])
        mandatory_fields = ['payment_mode_id', 'partner_vat']
        if lead['iban_other_owner']:
            mandatory_fields = [
                'payment_mode_id', 'iban_owner_vat', 'iban_owner_name',
                'iban_owner_email'
            ]

        info = self._check_and_get_mandatory_fields(cursor, uid, crml_id, mandatory_fields, other_fields=['iban'], context=context)

        pinfo = payment_mode_o.read(cursor, uid, info['payment_mode_id'][0], ['require_bank_account', 'type'])
        if not pinfo.get("require_bank_account") and not info['iban']:
            return _(u"No se ha especificado ningun IBAN y no es necessario crear uno.")
        elif pinfo.get("require_bank_account") and not info['iban']:
            raise osv.except_osv(
                _(u"Faltan Datos"), _(u"Se debe completar el campo 'Cuenta IBAN'.")
            )
        if lead['iban_other_owner']:
            iban_owner_vat = info['iban_owner_vat']
        else:
            iban_owner_vat = info['partner_vat']
        partner_id = partner_o.search(cursor, uid, [('vat', '=', iban_owner_vat)])
        if not partner_id:
            raise osv.except_osv(
                _(u"Faltan Datos"),
                _(u"Debe existir una empresa con codigo '{0}' para poder crear el IBAN {1}.").format(iban_owner_vat, info['iban'])
            )
        partner_id = partner_id[0]
        iban = info['iban'].replace(' ', '')
        bids = bank_o.search(cursor, uid, [
            ('iban', '=', iban), ('partner_id', '=', partner_id)
        ])
        if len(bids):
            return _(u"Se ha encontrado un IBAN con codigo {0} en la empresa {1}, no se creara una nueva cuenta bancaria.").format(info['iban'], iban_owner_vat)

        values = {
            'iban': info['iban'],
            'partner_id': partner_id,
            'owner_id': partner_id,
            'state': "iban"
        }

        if lead['iban_other_owner']:
            addr_ids = addr_o.search(cursor, uid, [
                ('partner_id', '=', partner_id),
                ('name', '=', info['iban_owner_name']),
                ('email', '=', info['iban_owner_email'])
            ])
            if not addr_ids:
                raise osv.except_osv(
                    _(u"Faltan Datos"),
                    _(u"Debe existir una direccion con el email {} y nombre {}.").format(
                        info['iban_owner_email'], info['iban_owner_name']
                    )
                )
            values['owner_address_id'] = addr_ids[0]

        country_code = info['iban'][:2]
        country_id = res_country.search(cursor, uid, [('code', '=', country_code)])
        if country_id:
            values['acc_country_id'] = country_id[0]
        bank_o.create(cursor, uid, values)
        return _(u"Se ha creado una nueva cuenta bancaria con IBAN {0}.").format(info['iban'])

    def _check_and_get_mandatory_fields(self, cursor, uid, crml_id, mandatory_fields=[], other_fields=[], context=None):
        if context is None:
            context = {}
        if isinstance(crml_id, (list, tuple)):
            crml_id = crml_id[0]
        if not mandatory_fields:
            res = {'id': crml_id}
        else:
            res = self.read(cursor, uid, crml_id, mandatory_fields)
        for f in mandatory_fields:
            if not res.get(f) and f in self._columns.keys() and self._columns[f]._type != 'boolean':
                field_name = self._columns[f].string
                raise osv.except_osv(_(u"Faltan Datos"), _(u"Se debe completar el campo '{0}'.").format(field_name))

        res.update(self.read(cursor, uid, crml_id, other_fields))
        del res['id']
        return res

    def create_entities(self, cursor, uid, ids, context={}):
        """
        Creació de les entitats: partner, soci, inversió, factura
        """
        if not isinstance(ids, (tuple, list)):
            ids = [ids]
        all_msgs = []
        for crm_id in ids:
            crm_msg = [""]
            msg = self.create_entity_partner(cursor, uid, ids, context)
            crm_msg.append(msg)
            msg = self.create_entity_soci(cursor, uid, ids, context)
            crm_msg.append(msg)
            msg = self.create_mandatory_apo(cursor, uid, ids, context)
            crm_msg.append(msg)
            all_msgs.append("\n * ".join(crm_msg))

        res = "\n\n\n".join(all_msgs)
        return res

    def remesar_factura(self, cursor, uid, ids, context={}):
        """ Remesar la factura """
        pass

    def validate_fields(self, cursor, uid, ids, context={}):
        """
            Comprovar que les dades entrades són correctes i
            la persona fisica/jurídica es pot fer socia
        """
        pass

    def create_new_member(self, cursor, uid, ids, context={}):
        """
            Si el lead és de tipus pagament per TPV: no fa res
            Si el lead és per pagar remesat: passa  l'estat que crea les entitats i retorna un codi soci.
        """
        pass

    def payment_successful(self, cursor, uid, ids, context={}):
        """
            Només per leads de tipus TPV.
            Passa a l'estat que crea les entitats, (que passi a pagat directe) i retorna codi soci
        """
        pass

    def payment_failed(self, cursor, uid, ids, context={}):
        """
            Només per leads tipus TPV.
            Passa a l'estat de lead canceŀlat.
        """
        pass

    _columns = {
        #Camps propis del lead
        'crm_id': fields.many2one('crm.case', required=True, ondelete='cascade'),
        'lead_payment_method': fields.char('Mètode de pagament', size=64),
        'lead_info': fields.text('Observacions'),
        'lead_redsys_response': fields.char('redsys_response', size=256),
        'partner_es_empresa': fields.function(_vat_es_empresa, method=True, type='boolean', string='Es Empresa'),

        #Camps Altres comptes
        'payment_mode_id': fields.many2one('payment.mode', 'Grup de pagament'),

        #Camps res.partner#
        'partner_nom': fields.char("Nom Client / Raó Social", size=256), #a webforms 'name', 'name' es un attr de crm.case, ja està agafat
        'partner_vat': fields.char('Nº de Document', size=11),
        #'active': True, # Aquest no cal
        'partner_comment': fields.char('Comentari', size=64),
        #'category_id': [(6, 0, c_soci)], # Auxpi no cal, ja posarem la categoria que toca
        'partner_lang': fields.selection(_lang_get, 'Idioma', size=5),
        'partner_comercial': fields.char('Trade name', size=64),
        'partner_date': fields.datetime('Date'),
        'partner_customer': fields.boolean('Client'),

        #Camps res.partner.address#
        #'name': member_name, ja el tenim
        'address_country_id': fields.many2one('res.country', 'Country'),
        'address_state_id': fields.many2one('res.country.state', 'State'), #TODO: Per a què?
        'address_email': fields.char('Email titular', size=256),
        'address_phone': fields.char('Telèfon', size=64),
        'address_mobile': fields.char('Mòbil', size=64),
        'address_zip': fields.char('CP', size=24),
        'address_nv': fields.char('Carrer', size=256),
        #'type': 'default', #Això no cal
        'address_municipi_id': fields.many2one('res.municipi', 'Municipi'),
        'address_poblacio_id': fields.many2one('res.poblacio', 'Població'),
        #Camps payment.mandate#
        #'debtor_name': member_name, # El tenim a 'nom'
        #'debtor_vat': vat, # El tenim a 'vat'
        #'debtor_address': '%s %s %s' % (
        #        request.form['adreca'],
        #        request.form['cp'],
        #        form_ciutat), # El tenim a 'nv'
        #'debtor_state': state_name, #tenim el country_id i necessitem accedir al name
        #'debtor_country': fields.char('Pais', size=64), #No cal, el create_from_form ja crea el mandato
        'iban': fields.char(string='Compte IBAN', size=34),
        #'reference': 'res.partner,%s', #TODO: el crearem nosaltres
        #'notes': _('QUOTA SOCI'), #TODO: el crearem nosaltres
        #'name': mandato, #això no cal, el default de l'ERP ja crida el mateix uuid4().hex
        #'creditor_code': fields.char(string='Creditor code', size=24), #No cal, el create_from_form ja crea el mandato
        #'date': mandato_date.strftime('%Y-%m-%d'), #és la mateixa que 'date'
        #'payment_type': 'one_payment' #TODO: ho posarem nosaltres pq sabem que la quota de soci és un sol pagamen
        'soci_id': fields.many2one('somenergia.soci', 'Soci'),
        'investment_id': fields.many2one('generationkwh.investment', 'Aportació Obligatòria'),
        'ip': fields.char(string='IP de la connexió', size=20),
    }

    _defaults = {

    }
    def call_check_vat(self, cr, uid, ids):
        for crm_lead in self.browse(cr, uid, ids):
            if not self.check_vat(cr, uid, crm_lead.partner_vat):
                return False
        return True

    def check_vat(self, cr, uid, vat, context=None):
        if not vat:
            return True
        partner_o = self.pool.get("res.partner")
        vat_country, vat_number = partner_o._split_vat(vat)
        if not partner_o.simple_vat_check(cr, uid, vat_country, vat_number):
            return False
        return True

SomSociCrmLead()
