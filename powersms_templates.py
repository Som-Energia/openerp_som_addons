from osv import osv, fields
from tools.translate import _

class PowersmsTemplates(osv.osv):
    "Templates for sending SMS"

    _name = "powersms.templates"
    _description = 'Power SMS Templates for Models'


    def _get_model_name(
            self, cursor, uid, template_ids, field_name, arg, context=None):
        res = {}
        pwm_templ_obj = self.pool.get('powersms.templates')
        for template_id in template_ids:
            model_id = pwm_templ_obj.read(
                cursor, uid, template_id, ['object_name'])['object_name']
            if not model_id:
                res[template_id] = False
                continue
            mod_name = self.pool.get('ir.model').read(
                cursor, uid, model_id[0], ['model'], context
            )['model']
            res[template_id] = mod_name
        return res


    _columns = {
        'name': fields.char('Name of Template', size=100, required=True),
        'object_name': fields.many2one('ir.model', 'Model'),
        'def_body_text':fields.text(
                'Standard Body (Text)',
                help="The text of the sms.",
                translate=True),
        'def_from':fields.char(
                'Remitent (From)',
                size=250,
                help="Public name of remitent"),
        'def_to':fields.char(
                'Recepients (To)',
                size=40,
                help="The recepient(s) of sms. "
                "Placeholders can be used here."),
        'enforce_from_account':fields.many2one(
                'powersms.core_accounts',
                string="Enforce From Account",
                help="SMS will be sent only from this account."),
        'ref_ir_act_window':fields.many2one(
                'ir.actions.act_window',
                'Window Action',
                readonly=True),
        'certificate':fields.boolean(
                'Use certificated SMS',
                help="The SMS will be sent certificated"),
        'lang':fields.char(
                'Language',
                size=250,
                help="The default language for the sms. "
                "Placeholders can be used here. "
                "eg. ${object.partner_id.lang}"),
        'model_object_field':fields.many2one(
                'ir.model.fields',
                string="Field",
                help="Select the field from the model you want to use."
                "\nIf it is a relationship field you will be able to "
                "choose the nested values in the box below.\n(Note: If "
                "there are no values make sure you have selected the "
                "correct model).",
                store=False),
        'auto_sms':fields.boolean('Auto SMS',
                help="Selecting Auto SMS will create a server "
                "action for you which automatically sends SMS after a "
                "new record is created.\nNote: Auto SMS can be enabled "
                "only after saving template."),
        'use_filter':fields.boolean(
                    'Active Filter',
                    help="This option allow you to add a custom python filter"
                    " before sending a sms"),
        'send_on_create': fields.boolean(
                'Send on Create',
                help='Sends a SMS when a new document is created.'),
        'send_on_write': fields.boolean(
                'Send on Update',
                help='Sends a SMS when a document is modified.'),
        'model_int_name': fields.function(
            _get_model_name, string='Model Internal Name',
            type='char', size=250, method=True
        ),
        'ref_ir_value':fields.many2one(
                'ir.values',
                'Wizard Button',
               readonly=True),
        'filter':fields.text(
                    'Filter',
                    help="The python code entered here will be excecuted if the"
                    "result is True the SMS will be send if it false the SMS "
                    "won't be send.\n"
                    "Example : o.type == 'out_invoice' and o.number and o.number[:3]<>'os_' "),
    }

    _defaults = {
        'ref_ir_act_window': False,
        'ref_ir_value': False,
    }
    _sql_constraints = [
        ('name', 'unique (name)', _('The template name must be unique!'))
    ]

PowersmsTemplates()