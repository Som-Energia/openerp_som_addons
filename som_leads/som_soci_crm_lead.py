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


    addr_fields = [
        'zip',
        'id_municipi',
        'id_poblacio',
        'tv',
        'nv',
        'pnp',
        'bq',
        'es',
        'pt',
        'pu',
        'cpo',
        'cpa',
        'aclarador',
        'apartat_correus',
    ]

    lead_titular_adr_to_adr = {
        'titular_zip': 'zip',
        'titular_id_municipi': 'id_municipi',
        'titular_id_poblacio': 'id_poblacio',
        'titular_tv': 'tv',
        'titular_nv': 'nv',
        'titular_pnp': 'pnp',
        'titular_bq': 'bq',
        'titular_es': 'es',
        'titular_pt': 'pt',
        'titular_pu': 'pu',
        'titular_cpo': 'cpo',
        'titular_cpa': 'cpa',
        'titular_aclarador': 'aclarador',
        'titular_apartat_correus': 'apartat_correus',
        'titular_email': 'email',
        'titular_phone': 'phone',
        'titular_mobile': 'mobile'
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
        self.update_current_stage_validations(cursor, uid, res_id, context=context)
        return res_id

    def write(self, cursor, uid, ids, vals, context=None):
        if context is None:
            context = {}
        if vals is None:
            vals = {}

        if vals.get("stage_id"):
            self.validate_current_stage(cursor, uid, ids, context=context)

        self._clean_values(cursor, uid, vals, context=context)

        res = super(osv.osv, self).write(cursor, uid, ids, vals, context)

        if vals.get("stage_id"):
            self.update_current_stage_validations(cursor, uid, ids, context=context)
        return res

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

    def stage_next(self, cr, uid, ids, context=None):
        self.validate_current_stage(cr, uid, ids, context=context)

        crm_obj = self.pool.get('crm.case')
        crm_ids = [crm_tala_data['crm_id'][0] for crm_tala_data in self.read(cr, uid, ids, ['crm_id'])]
        res = crm_obj.stage_next(cr, uid, crm_ids, context)
        self.update_current_stage_validations(cr, uid, ids, context=context)
        return res

    def stage_previous(self, cr, uid, ids, context=None):
        self.validate_current_stage(cr, uid, ids, context=context)

        crm_obj = self.pool.get('crm.case')
        crm_ids = [crm_tala_data['crm_id'][0] for crm_tala_data in self.read(cr, uid, ids, ['crm_id'])]
        res = crm_obj.stage_previous(cr, uid, crm_ids, context)
        self.update_current_stage_validations(cr, uid, ids, context=context)
        return res

    def validate_current_stage(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        cl_ids = ids
        if not isinstance(ids, (list, tuple)):
            cl_ids = [ids]

        for cl_id in cl_ids:
            current_stage = self.read(cr, uid, cl_id, ['stage_id'])
            if not current_stage['stage_id']:
                return True
            current_stage = current_stage['stage_id'][0]
            val_o = self.pool.get("crm.stage.validation")
            vids = val_o.search(cr, uid, [
                ('crm_lead_id', '=', cl_id),
                ('validated', '!=', True),
                '|', ('stage_id', '=', current_stage), ('stage_id', '=', None)
            ])
            if len(vids):
                val_texts = [x['name'] for x in val_o.read(cr, uid, vids, ['name'])]
                err_msg = ", ".join(val_texts)
                raise osv.except_osv(_(u"Operacion no permitida!"), _(u"No se puede cambiar de stage hasta que no se hayan completado o eliminado las siguientes validaciones: {0}").format(err_msg))

    def update_current_stage_validations(self, cursor, uid, ids, context=None):
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        if context is None:
            context = {}
        template_o = self.pool.get('crm.stage.validation.template')
        val_o = self.pool.get("crm.stage.validation")
        sp = [('stage_id', '=', None)]
        for vals in self.read(cursor, uid, ids, ['stage_id']):
            current_sp = sp[:]
            if vals.get("stage_id"):
                current_sp = ['|'] + current_sp + [('stage_id', '=', vals.get("stage_id")[0])]
            for default_val in template_o.search(cursor, uid,  current_sp, context=context):
                val_o.create_from_template(cursor, uid, vals['id'], default_val, context=context)
        return True

    def _vat_es_empresa(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = {}
        partner_o = self.pool.get("res.partner")
        for inf in self.read(cr, uid, ids, ['titular_vat']):
            vat = inf['titular_vat']
            res[inf['id']] = partner_o.is_enterprise_vat(vat) if vat else False
        return res

    def create_entities(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        all_msgs = []
        gid = self.pool.get("res.users").read(cursor, uid, uid, ['groups_id'])['groups_id'][0]
        with Sudo(uid=uid, gid=gid):
            for crm_id in ids:
                crm_msg = [""]

                self.validate_current_stage(cursor, 1, crm_id, context=context)

                msg = self.create_entity_distribuidora(cursor, 1, crm_id, context=context)
                crm_msg.append(msg)

                msg = self.create_entity_cups(cursor, 1, crm_id, context=context)
                crm_msg.append(msg)

                msg = self.create_entity_titular(cursor, 1, crm_id, context=context)
                crm_msg.append(msg)

                msg = self.create_entity_iban(cursor, 1, crm_id, context=context)
                crm_msg.append(msg)

                msg = self.create_entity_polissa(cursor, 1, crm_id, context=context)
                crm_msg.append(msg)

                msg = self.create_entity_autoconsum(cursor, 1, crm_id, context=context)
                crm_msg.append(msg)

                all_msgs.append("\n * ".join(crm_msg))

        res = "\n\n\n".join(all_msgs)
        # Netegem cache per refrescar les regles dels colaboradors
        cache.clean_caches_for_db(cursor.dbname)
        return res

    def create_entity_titular(self, cursor, uid, crml_id, context=None):
        if context is None:
            context = {}
        if isinstance(crml_id, (list, tuple)):
            crml_id = crml_id[0]

        partner_o = self.pool.get("res.partner")
        adr_o = self.pool.get("res.partner.address")
        municipi_o = self.pool.get("res.municipi")

        adr_titular_fields = self.lead_titular_adr_to_adr.keys()
        opt_fields = adr_titular_fields[:]
        opt_fields.extend(['titular_cognom2', 'lang'])
        mandatory_fields = ['titular_vat', 'titular_nom', 'use_cont_address']
        lead = self.read(cursor, uid, crml_id, ['titular_es_empresa', 'iban_other_owner'])
        es_empresa = lead['titular_es_empresa']
        if not es_empresa:
            mandatory_fields.append('titular_cognom1')
        else:
            opt_fields.append('titular_cognom1')
        if lead['iban_other_owner']:
            mandatory_fields += ['iban_owner_vat', 'iban_owner_name', 'iban_owner_email']
        info = self._check_and_get_mandatory_fields(cursor, uid, crml_id, mandatory_fields, opt_fields, context=context)

        if es_empresa:
            new_name = info['titular_nom']
        else:
            conf_obj = self.pool.get('res.config')
            name_as_dict = {
                "N": info['titular_nom'], "C1": info['titular_cognom1'] or "", "C2": info['titular_cognom2'] or ""
            }
            name_struct = conf_obj.get(cursor, uid, 'partner_name_format', 'C1 C2, N')
            if name_struct == 'C1 C2, N':
                name_formatter = "{C1} {C2}, {N}"
            else:
                name_formatter = "{N} {C1} {C2}"
            new_name = name_formatter.format(**name_as_dict)
            new_name = new_name.strip()
            new_name = new_name.replace(" ,", ",")

        aid = None
        tids = partner_o.search(cursor, uid, [('vat', '=', info['titular_vat'])])
        if len(tids):
            tid = tids[0]
            res = _(u"Se ha encontrado un titular con numero de documento {0}, no se creara una nueva ficha de empresa. ").format(info['titular_vat'])
            # Comprovem si l'adreça tamb existeix
            sp = [('partner_id', '=', tid)]
            for f, val in info.iteritems():
                if f not in self.lead_titular_adr_to_adr.keys():
                    continue
                if isinstance(val, (list, tuple)):
                    val = val[0]
                sp.append((self.lead_titular_adr_to_adr.get(f), '=', val))
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
                'name': new_name,
                'vat': info['titular_vat'],
                'lang': info['lang']
            }
            tid = partner_o.create(cursor, uid, create_vals)
            res = _(u"Se ha creado un nuevo titular con numero de documento {0}. ").format(info['titular_vat'])

        if tid:
            self.write(cursor, uid, [crml_id], {'partner_id': tid}, context=context)

        if crear_address:
            create_vals = {'name': new_name, 'partner_id': tid}
            for fname, fval in info.iteritems():
                if not fval:
                    continue
                if isinstance(fval, (list, tuple)):
                    fval = fval[0]
                if fname in ['titular_nom', 'titular_cognom1', 'titular_cognom2']:
                    continue
                create_vals[self.lead_titular_adr_to_adr.get(fname, fname)] = fval
            if create_vals.get("id_municipi") and not create_vals.get("state_id"):
                create_vals["state_id"] = municipi_o.read(cursor, uid, create_vals.get("id_municipi"), ['state'])['state'][0]
            aid = adr_o.create(cursor, uid, create_vals)
            res += _(u"Ninguna direccion del titular coincide con la actual, se ha creado una nueva direccion.")

        if info['use_cont_address']:
            cont_titular_fields = self.lead_titular_adr_to_adr.keys()
            cont_titular_fields = ["cont_"+x for x in cont_titular_fields]
            cont_titular_fields.append("cont_titular_nom")
            alt_info = self._check_and_get_mandatory_fields(cursor, uid, crml_id, [], cont_titular_fields, context=context)
            ctx = context.copy()
            ctx['extra_match_fields'] = ["cont_titular_nom"]
            adrids = self.match_address_id_from_lead(cursor, uid, crml_id, address_prefix="cont_", partner_id=tid, context=ctx)
            if not len(adrids):
                create_vals = {'name': alt_info['cont_titular_nom'] or new_name, 'partner_id': tid}
                for fname, fval in alt_info.iteritems():
                    if not fval:
                        continue
                    if isinstance(fval, (list, tuple)):
                        fval = fval[0]
                    if fname in ['cont_titular_nom', 'cont_titular_cognom1', 'cont_titular_cognom2']:
                        continue
                    create_vals[self.lead_titular_adr_to_adr.get(fname.replace("cont_", ""), fname)] = fval
                if create_vals.get("id_municipi") and not create_vals.get("state_id"):
                    create_vals["state_id"] = municipi_o.read(cursor, uid, create_vals.get("id_municipi"), ['state'])['state'][0]
                adr_o.create(cursor, uid, create_vals)
                res += _(u"Se ha creado una nueva direccion de contacto.")

        if lead['iban_other_owner']:
            adrids = []
            tids = partner_o.search(cursor, uid, [
                ('vat', '=', info['iban_owner_vat'])
            ])
            if tids:
                tid = tids[0]
                res = _(
                    u"Se ha encontrado un partner con numero de documento {0}, no se creara una nueva ficha de empresa. ").format(
                    info['iban_owner_vat'])
                # Comprovem si l'adreça tamb existeix
                sp = [
                    ('partner_id', '=', tid),
                    ('email', '=', info['iban_owner_email']),
                    ('name', '=', info['iban_owner_name'])
                ]
                adrids = adr_o.search(cursor, uid, sp)
                if adrids:
                    res += _(
                        u"La direccion del propietario del IBAN encontrado coincide con la actual, no se creara una nueva direccion.")
            else:
                create_vals = {
                    'name': info['iban_owner_name'],
                    'vat': info['iban_owner_vat'],
                    'lang': info['lang']
                }
                tid = partner_o.create(cursor, uid, create_vals)
                res = _(
                    u"Se ha creado un nuevo partner propietario IBAN con numero de documento {0}. ").format(
                    info['iban_owner_vat'])
            if not adrids:
                adr_o.create(cursor, uid, {
                    'partner_id': tid,
                    'name': info['iban_owner_name'],
                    'email': info['iban_owner_email']
                })
                res += _(u"Ninguna direccion coincide con el propietario del IBAN, se ha creado una nueva direccion.")

        if aid:
            self.write(cursor, uid, [crml_id], {'partner_address_id': aid}, context=context)

        return res

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
        mandatory_fields = ['payment_mode_id', 'titular_vat']
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
            iban_owner_vat = info['titular_vat']
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


    _columns = {
        'crm_id': fields.many2one('crm.case', required=True, ondelete='cascade'),
        'lang': fields.selection(_lang_get, 'Idioma', size=5),
        # Dades facturacio del contracte
        'iban_owner_vat': fields.char('NIF titular IBAN', size=11),
        'iban_owner_name': fields.char('Nombre titular IBAN', size=256),
        'iban_owner_email': fields.char('Email titular IBAN', size=256),
        'iban': fields.char(string='Cuenta IBAN', size=34, mandatory=True),
        'payment_mode_id': fields.many2one('payment.mode', 'Grupo de pago', mandatory=True),
        # Dades del Titular
        'titular_vat': fields.char('Nº de Documento', size=11, mandatory=True),
        'titular_es_empresa': fields.function(_vat_es_empresa, method=True, type='boolean', string='Es Empresa'),
        'titular_nom': fields.char("Nombre Cliente / Razón Social", size=256, mandatory=True),
        'titular_cognom1': fields.char("Apellido 1", size=30, mandatory=True),
        'titular_cognom2': fields.char("Apellido 2", size=30),
        # Dades de contacte del Titular
        'tipus_vivenda': fields.selection([('habitual', 'Habitual'), ('no_habitual', 'No habitual')], string='Tipo vivienda', mandatory=True),
        'titular_zip': fields.char('Codigo Postal', change_default=True, size=24),
        'titular_tv': fields.many2one('res.tipovia', 'Tipo Via'),
        'titular_nv': fields.char('Calle', size=256),
        'titular_pnp': fields.char('Número', size=10),
        'titular_bq': fields.char('Bloque', size=4),
        'titular_es': fields.char('Escalera', size=10),
        'titular_pt': fields.char('Planta',size=10),
        'titular_pu': fields.char('Puerta', size=10),
        'titular_cpo': fields.char('Poligono', size=10),
        'titular_cpa': fields.char('Parcela', size=10),
        'titular_aclarador': fields.char('Aclarador', size=256),
        'titular_id_municipi': fields.many2one('res.municipi', 'Municipio'),
        'titular_id_poblacio': fields.many2one('res.poblacio', 'Población'),
        'titular_apartat_correus': fields.char("Apartado de Correos", size=5),
        'titular_email': fields.char('E-Mail', size=240, mandatory=True),
        'titular_phone': fields.char('Telefono', size=64, mandatory=True),
        'titular_mobile': fields.char('Mobil', size=64, mandatory=True),
    }

    def call_check_vat(self, cr, uid, ids):
        for crm_lead in self.browse(cr, uid, ids):
            if not self.check_vat(cr, uid, crm_lead.titular_vat):
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

    def _vat_es_empresa(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = {}
        partner_o = self.pool.get("res.partner")
        for inf in self.read(cr, uid, ids, ['titular_vat']):
            vat = inf['titular_vat']
            res[inf['id']] = partner_o.is_enterprise_vat(vat) if vat else False
        return res

SomSociCrmLead()



