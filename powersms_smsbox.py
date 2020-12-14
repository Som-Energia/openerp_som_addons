from osv import osv, fields

class PowersmsSMSbox(osv.osv):
    _name = "powersms.smsbox"
    _description = 'Power SMS SMSbox included all type inbox,outbox,junk..'
    _rec_name = "psms_subject"
    _order = "date_sms desc"

    _columns = {
            'psms_account_id' :fields.many2one(
                            'powersms.core_accounts',
                            'User account',
                            required=True),
            'psms_from':fields.char(
                            'From',
                            size=64),
            'date_sms':fields.datetime(
                            'Rec/Sent Date'),
            'psms_to':fields.char(
                            'Recepient (To)',
                            size=250,),
            'psms_body_text':fields.text(
                            'Standard Body (Text)'),
            'state':fields.selection([
                            ('read', 'Read'),
                            ('unread', 'Un-Read'),
                            ('na', 'Not Applicable'),
                            ('sending', 'Sending'),
                            ('sent', 'Sent'),
                            ], 'Status', required=True),
            'folder':fields.selection([
                            ('inbox', 'Inbox'),
                            ('drafts', 'Drafts'),
                            ('outbox', 'Outbox'),
                            ('trash', 'Trash'),
                            ('followup', 'Follow Up'),
                            ('sent', 'Sent Items'),
                            ], 'Folder', required=True),
            'history':fields.text(
                            'History',
                            readonly=True,
                            store=True),
        }

    _defaults = {
        'state': lambda * a: 'na',
        'folder': lambda * a: 'outbox',
    }

PowersmsSMSbox()