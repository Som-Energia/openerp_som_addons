from osv import osv, fields
import re

class PowersmsSMSbox(osv.osv):
    _name = "powersms.smsbox"
    _description = 'Power SMS SMSbox included all type inbox,outbox,junk..'
    _rec_name = "psms_subject"
    _order = "date_sms desc"

    def check_mobile(self, mobile_number):
        if not re.match(r"((?:\+34)*|(?:0034)*)6[0-9]{8}|((?:\+34)*|(?:0034)*)7[0-9]{8}", mobile_number):
            return False
        return True

    def is_valid(self, cursor, uid, sms_id, context=None):
        mail = self.read(cursor, uid, sms_id, ['psms_to'], context)
        return self.check_mobile(mail['psms_to'])

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