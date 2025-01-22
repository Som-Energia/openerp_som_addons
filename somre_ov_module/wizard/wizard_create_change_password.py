# -*- coding: utf-8 -*-
from osv import osv, fields
import random
import string
import requests
import json
from tools import config

from ..models.exceptions import FailSendEmail


class WizardCreateChangePassword(osv.osv_memory):

    """Classe per gestionar el canvi de contrasenya
    """

    _name = "wizard.create.change.password"

    def default_get(self, cursor, uid, fields, context=None):
        res = super(WizardCreateChangePassword, self).default_get(cursor, uid, fields, context)

        ov_users_obj = self.pool.get('somre.ov.users')
        active_ids = context.get('active_ids')

        info = '{} ({}): \n{}'.format(
            'Es generarant contrasenyes pels següents partners',
            len(active_ids),
            '\n'.join([ov_users_obj.read(cursor, uid, x, ['name'])['name'] for x in active_ids])
        )

        res.update({
            'initial_info': info,
        })
        return res

    def generatePassword(self):
        # Generate a list of random characters
        characters = [random.choice(string.ascii_letters + string.digits) for _ in range(8)]
        characters += [random.choice(string.punctuation) for _ in range(2)]

        # Shuffle the list of characters
        random.shuffle(characters)
        # Return the shuffled list of characters as a string
        return ''.join(characters)

    def send_password_email(self, cursor, uid, ov_user, context=None):
        ir_model_data = self.pool.get('ir.model.data')
        power_email_tmpl_obj = self.pool.get('poweremail.templates')

        template_id = ir_model_data.get_object_reference(
            cursor, uid, 'somre_ov_module', 'email_create_change_password'
        )[1]
        template = power_email_tmpl_obj.read(cursor, uid, template_id)

        account_obj = self.pool.get('poweremail.core_accounts')

        email_from = False
        email_account_id = 'info@somenergia.coop'
        if template.get('enforce_from_account', False):
            email_from = template.get('enforce_from_account')[0]
        if not email_from:
            email_from = account_obj.search(cursor, uid, [('email_id', '=', email_account_id)])[0]

        try:
            wiz_send_obj = self.pool.get('poweremail.send.wizard')
            ctx = {
                'active_ids': [ov_user.id],
                'active_id': ov_user.id,
                'template_id': template_id,
                'src_model': 'somre.ov.users',
                'src_rec_ids': [ov_user.id],
                'from': email_from,
                'state': 'single',
                'priority': '0',
            }
            params = {'state': 'single', 'priority': '0', 'from': ctx['from']}
            wiz_id = wiz_send_obj.create(cursor, uid, params, ctx)
            wiz_send_obj.send_mail(cursor, uid, [wiz_id], ctx)

        except Exception as e:
            raise FailSendEmail(e.message)

    def save_privisioning_data(self, cursor, uid, partner_id, password):
        partner_o = self.pool.get("res.partner")
        try:
            partner = partner_o.browse(cursor, uid, partner_id)
            data = {
                "username": partner.vat,
                "password": password,
                "email": partner.address[0].email if partner.address else 'NO EMAIL',
                "fullname": partner.name,
            }
            headers = {
                'Accept': 'application/json',
                'X-API-KEY': config.get('api_key_ov_representa', False)
            }
            url = config.get('api_url_ov_representa', False)

            res = requests.post(url, data=json.dumps(data), headers=headers)
            return res.status_code == 200
        except Exception:
            return False

    def action_create_change_password(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        ov_users_ids = context.get("active_ids")
        ov_users_o = self.pool.get("somre.ov.users")

        error_info = []
        for ov_user_id in ov_users_ids:
            ov_user = ov_users_o.browse(cursor, uid, ov_user_id)
            password = self.generatePassword()
            result = self.save_privisioning_data(cursor, uid, ov_user_id, password)
            if not result:
                info = "{} ({})\n".format(str(int(ov_user_id)), 'Error al guardar la contrasenya')
                error_info.append(info)
                continue

            ov_users_o.write(cursor, uid, [ov_user_id], {'initial_password': password})
            try:
                self.send_password_email(cursor, uid, ov_user)
            except FailSendEmail:
                info = "{} ({})\n".format(str(int(ov_user_id)), "Error al generar/enviar l'email")
                error_info.append(info)
                continue

        values = {
            'state': 'done'
        }

        if error_info:
            values['info'] = "{}: \n {}".format(
                'Error generant contrasenyes pels següents partners',
                ','.join([x for x in error_info])
            )
        else:
            values['info'] = "{}".format('Contrasenyes generades')

        self.write(cursor, uid, ids, values)
        return True

    _columns = {
        'state': fields.char('State', size=16),
        'info': fields.text('Info', size=4000),
        'initial_info': fields.text('Initial info', size=4000),
    }

    _defaults = {
        'state': lambda *a: 'init',
    }


WizardCreateChangePassword()
