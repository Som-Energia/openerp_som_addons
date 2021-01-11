from osv import osv, fields
import tools

class PowersmsSendWizard(osv.osv_memory):
    _name = 'powersms.send.wizard'
    _description = 'This is the wizard for sending SMS'
    _rec_name = "subject"

    def _get_accounts(self, cr, uid, context=None):
        if context is None:
                context = {}
        accounts_obj = self.pool.get('powersms.core_accounts')
        template = self._get_template(cr, uid, context)
        if not template:
            return []

        if template.enforce_from_account:
            return [(template.enforce_from_account.id, '%s (%s)' % (template.enforce_from_account.name, template.enforce_from_account.tel_id))]
        else:
            account_ids = accounts_obj.search(cr, uid, [('state','=','approved')])
            return [
                (acc['id'], "{} ({})".format(acc['name'], acc['tel_id']))
                for acc in accounts_obj.read(cr, uid, account_ids, ['name','tel_id'])
            ]


    def get_value(self, cursor, user, template, message, context=None, id=None):
        """Gets the value of the message parsed with the content of object id (or the first 'src_rec_ids' if id is not given)"""
        pwm_templ_obj = self.pool.get('powersms.templates')
        if not message:
            return ''
        if not id:
            id = context['src_rec_ids'][0]
        return pwm_templ_obj.get_value(cursor, user, id, message, template, context)

    def _get_template(self, cr, uid, context=None):
        if context is None:
            context = {}
        if not 'template_id' in context:
            return None
        template_obj = self.pool.get('powersms.templates')
        if 'template_id' in context.keys():
            template_ids = template_obj.search(cr, uid, [('id','=',context['template_id'])], context=context)
        if not template_ids:
            return None

        template = template_obj.browse(cr, uid, template_ids[0], context)

        lang = self.get_value(cr, uid, template, template.lang, context)
        if lang:
            # Use translated template if necessary
            ctx = context.copy()
            ctx['lang'] = lang
            template = template_obj.browse(cr, uid, template.id, ctx)
        return template


    def _get_template_value(self, cr, uid, field, context=None):
        template = self._get_template(cr, uid, context)
        if not template:
            return False
        if len(context['src_rec_ids']) > 1: # Multiple Mail: Gets original template values for multiple email change
            return getattr(template, field)
        else: # Simple Mail: Gets computed template values
            return self.get_value(cr, uid, template, getattr(template, field), context)


    def send_sms(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        smsbox_obj = self.pool.get('powersms.smsbox')
        folder = context.get('folder', 'outbox')
        values = {'folder': folder}

        sms_ids = self.save_to_smsbox(cursor, uid, ids, context)

        if sms_ids:
            for sms_id in sms_ids:
                if not smsbox_obj.is_valid(cursor, uid, sms_id):
                    values['folder'] = 'drafts'
                else:
                    values['folder'] = folder
                smsbox_obj.write(cursor, uid, [sms_id], values, context)

        return {'type': 'ir.actions.act_window_close'}


    def save_to_smsbox(self, cr, uid, ids, context=None):
        model_obj = self.pool.get('ir.model')

        if context is None:
            context = {}
        def get_end_value(id, value):
            if len(context['src_rec_ids']) > 1: # Multiple Mail: Gets value from the template
                return self.get_value(cr, uid, template, value, context, id)
            else:
                return value

        sms_ids = []
        template = self._get_template(cr, uid, context)
        screen_vals = self.read(cr, uid, ids[0], [], context)
        if isinstance(screen_vals, list): # Solves a bug in v5.0.16
            screen_vals = screen_vals[0]
        report_record_ids = context['src_rec_ids'][:]

        for id in context['src_rec_ids']:
            accounts = self.pool.get('powersms.core_accounts').read(cr, uid, screen_vals['account'], context=context)
            vals = {
                'psms_from': screen_vals['from'],
                'psms_to': get_end_value(id, screen_vals['to']),
                'psms_body_text': get_end_value(id, screen_vals['body_text']),
                'psms_account_id': screen_vals['account'],
                'state':'na',
            }

            #Create partly the mail and later update attachments
            ctx = context.copy()
            ctx.update({'src_rec_id': id})
            sms_id = self.pool.get('powersms.smsbox').create(cr, uid, vals, ctx)
            sms_ids.append(sms_id)

           # Ensure report is rendered using template's language. If not found, user's launguage is used.
            ctx = context.copy()
            if template.lang:
                ctx['lang'] = self.get_value(cr, uid, template, template.lang, context, id)
                lang = self.get_value(cr, uid, template, template.lang, context, id)
                if len(self.pool.get('res.lang').search(cr, uid, [('name','=',lang)], context = context)):
                    ctx['lang'] = lang
            if not ctx.get('lang', False) or ctx['lang'] == 'False':
                ctx['lang'] = self.pool.get('res.users').read(cr, uid, uid, ['context_lang'], context)['context_lang']

        return sms_ids


    _columns = {
        'ref_template':fields.many2one('powersms.templates','Template',readonly=True),
        'rel_model':fields.many2one('ir.model','Model',readonly=True),
        'from':fields.char('From Account', size=100, required=True),
        'to':fields.char('To',size=250,required=True),
        'body_text':fields.text('Body',),
        'account': fields.selection(_get_accounts, 'Account', select=True, required=True),
    }

    _defaults = {
        'rel_model': lambda self,cr,uid,ctx: self.pool.get('ir.model').search(cr,uid,[('model','=',ctx['src_model'])],context=ctx)[0],
        'to': lambda self,cr,uid,ctx: self.pool.get('powersms.core_accounts').filter_send_sms(cr, uid, self._get_template_value(cr, uid, 'def_to', ctx)),
        'from': lambda self,cr,uid,ctx: self._get_template_value(cr, uid, 'def_from', ctx),
        'body_text':lambda self,cr,uid,ctx: self._get_template_value(cr, uid, 'def_body_text', ctx),
        'ref_template':lambda self,cr,uid,ctx: self._get_template(cr, uid, ctx).id,
    }

PowersmsSendWizard()