
##imports

from ast import Param
import base64
from fileinput import filename
from genericpath import isfile
import io
from quopri import encodestring
from ssl import DefaultVerifyPaths
import pooler
from osv import osv, fields
from tools.translate import _
import json
import os
from datetime import datetime
import subprocess
import netsvc
import zipfile
from os.path import expanduser


## Describes the module that executes a general task
# @author Ikram Ahdadouche El Idrissi
# @author Dalila Jbilou Kouhous


LOGGER = netsvc.Logger()


## Describes the module and contains the function that changes the password

class WizardExecutarTasca(osv.osv_memory):

     ## Module name 
    _name= 'wizard.executar.tasca'

    """Function that gets gets that task, task result and task step, and executes a task
        @param self The object pointer
        @param cursor The database pointer
        @param uid The current user
        @param ids The tasks ids selected
        @param context None certain data to pass
        @return server action module (act_windows_close)
    """

    def executar_tasca(self, cursor, uid, ids, context=None):
        ##obtenim l'objecte tasca
        task = self.pool.get('som.crawlers.task')
        if not context:
            return False
        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        active_ids = context.get('active_ids',[])

        for id in active_ids:
            #obtenim una tasca
            task.executar_tasca(cursor,uid,id,context)

        return {'type': 'ir.actions.act_window_close'}

WizardExecutarTasca()
