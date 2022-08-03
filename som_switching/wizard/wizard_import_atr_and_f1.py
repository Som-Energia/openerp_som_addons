# -*- coding: utf-8 -*-
import zipfile
import glob

from osv import osv

class WizardImportAtrAndF1(osv.osv_memory):

    _name = 'wizard.import.atr.and.f1'
    _inherit = 'wizard.import.atr.and.f1'

    def _create_tmp_zip(self, cursor, uid, ids, directory, prefix, context=None):
        """
        Creates a temporal zip file and returns it's **opened** handler.
        :param prefix: prefix of the temporal zip name
        """

        if prefix == 'F1_':
            wizard = self.browse(cursor, uid, ids[0])
            tmp_filename = wizard.filename
            if '/' in tmp_filename:
                tmp_filename = tmp_filename.split('/')[-1] #when file from massive_importer file_name can contains subfolders
            tmp_zip = open('{temporal_folder}/{pref}{filename}'.format(
                temporal_folder = directory,
                pref=prefix,
                filename = tmp_filename),
                'w+'
            )
            zip_handler = zipfile.ZipFile(tmp_zip, 'w')
        else:
            zip_handler = super(WizardImportAtrAndF1, self)._create_tmp_zip(
                cursor, uid, ids, directory, prefix, context
            )
        return zip_handler

WizardImportAtrAndF1()