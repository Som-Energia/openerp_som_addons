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
            tmp_zip = open('{temporal_folder}/{filename}'.format(
                temporal_folder = directory,
                filename = wizard.filename),
                'w+'
            )
            zip_handler = zipfile.ZipFile(tmp_zip, 'w')
        else:
            zip_handler = super(WizardImportAtrAndF1, self)._create_tmp_zip(
                cursor, uid, ids, directory, prefix, context
            )
        return zip_handler

    @staticmethod
    def _get_b64_zip_files(zip_path, context=None):

        _type = context['type']
        if _type == 'F1':
            zip_filename = glob.glob(
                '{path}/*.zip.b64'.format(path=zip_path)
            )[0]
        else:
            zip_filename = glob.glob(
                '{path}/{type}_*.zip.b64'.format(path=zip_path, type=_type)
            )[0]
        with open(zip_filename, 'r') as zip_handler:
            return zip_filename, zip_handler.read()

WizardImportAtrAndF1()