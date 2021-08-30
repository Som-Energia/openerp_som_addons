# -*- coding: utf-8 -*-

from gestionatr.utils import get_description
from ..component_utils import dateformat
from ..ProcesR1 import ProcesR1
from tools.translate import _

class R101(ProcesR1.ProcesR1):
    def __init__(self):
        ProcesR1.ProcesR1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesR1.ProcesR1.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'R101'
        result['tipus_reclamacio'] = step.subtipus_id.name + " - " + step.subtipus_id.desc if step.subtipus_id else ''
        result['text'] = step.comentaris
        result['documents_adjunts'] = [(get_description(doc.type, "TABLA_61"), doc.url) for doc in step.document_ids]
        result['variables_aportacio'] = []
        for var_apo in step.vars_aportacio_info_ids:
            result['variables_aportacio'].append({
                    'valor': var_apo.valor,
                    'variable': get_description(var_apo.variable, "TABLA_76"),
                    'descripcio': var_apo.desc_peticio_info,
                    'tipus': get_description(var_apo.tipus_info, "TABLA_85"),
                })

        result['reclamacions'] = []

        for reclama in step.reclamacio_ids:
            lectures = []
            for lect in reclama.lect_ids:
                lectures.append({
                    'Lectura': lect.lectura,
                    'Magnitud': lect.magnitud,
                    'Nom': lect.name,
                    })
            aten_incorr = False
            concept_facturat = False
            par_contr = False
            if reclama.tipus_atencio_incorrecte:
                aten_incorr=get_description(reclama.tipus_atencio_incorrecte, "TABLA_87_simple")
            if reclama.tipus_concepte_facturat:
                concept_facturat=get_description(reclama.tipus_concepte_facturat, "TABLA_77")
            if reclama.parametre_contractacio:
                par_contr=get_description(reclama.parametre_contractacio, "TABLA_79")
            result['reclamacions'].append({
                _(u'Codi dh'): reclama.codi_dh,
                _(u'Codi incidència'): reclama.codi_incidencia,
                _(u'Codi postal'): reclama.codi_postal,
                _(u'Codi sol·licitud'): reclama.codi_sollicitud,
                _(u'Codi sol·licitud reclamació'): reclama.codi_sollicitud_reclamacio,
                _(u'Concepte disconformitat'): reclama.concepte_disconformitat,
                _(u'Cont email'): reclama.cont_email,
                _(u'Cont nom'): reclama.cont_nom,
                _(u'Cont prefix'): reclama.cont_prefix,
                _(u'Cont telèfon'): reclama.cont_telefon,
                _(u'Data fins'): reclama.data_fins,
                _(u'Data incident'): reclama.data_incident,
                _(u'Data inici'): reclama.data_inici,
                _(u'Data lectura'): reclama.data_lectura,
                _(u'Descripció ubicació'): reclama.desc_ubicacio,
                _(u'IBAN'): reclama.iban,
                _(u'Import reclamat'): reclama.import_reclamat,
                _(u'Municipi'): reclama.municipi,
                _(u'Número expedient escomesa'): reclama.num_expedient_escomesa,
                _(u'Número expedient frau'): reclama.num_expedient_frau,
                _(u'Número factura'): reclama.num_factura,
                _(u'Paràmetre contractació'): par_contr,
                _(u'Població'): reclama.poblacio,
                _(u'Província'): reclama.provincia,
                _(u'Tipus atenció incorrecte'): aten_incorr,
                _(u'Tipus concepte facturat'): concept_facturat,
                _(u'Lectures'): lectures
            })
        return result