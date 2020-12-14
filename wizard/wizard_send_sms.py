from osv import osv, fields

class PowersmsSendWizard(osv.osv_memory):
    _name = 'powersms.send.wizard'
    _description = 'This is the wizard for sending SMS'
    _rec_name = "subject"


PowersmsSendWizard()