# -*- coding: utf-8 -*-
from tools.translate import _
from osv import osv
from base_extended.wizard.wizard_model_list_from_file import RES_MODEL_SELECTION

if ("giscedata.facturacio.extra", _(u"Extra Lines")):  # noqa: F634
    RES_MODEL_SELECTION.append(
        ("giscedata.facturacio.extra", _(u"Extra Lines")),
    )


class WizardModelListFromFile(osv.osv_memory):
    """Wizard"""

    _name = "wizard.model.list.from.file"
    _inherit = "wizard.model.list.from.file"


WizardModelListFromFile()
