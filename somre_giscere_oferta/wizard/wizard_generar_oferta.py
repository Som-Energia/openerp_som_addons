# -*- coding: utf-8 -*-
from __future__ import absolute_import
from ast import literal_eval
from datetime import datetime, timedelta
from osv import osv
import logging
import time


MAX_RETRIES = 3  # OMIE send retries by offer


class WizardGisceReGenerarOfertaSom(osv.osv_memory):

    _name = 'wizard.giscere.generar.oferta'
    _inherit = 'wizard.giscere.generar.oferta'

    def send_email(self, cursor, uid, info, errors, energia, context=None):
        """
        Generates an e-mail with info, errors and energy info
        :param cursor: OpenERP DB Cursor
        :param uid: OpenERP User ID
        :param info: list
        :param errors: list
        :param energia: list
        :param context: OpenERP Current Context
        :return:
        """
        if context is None:
            context = {}

        imd_obj = self.pool.get('ir.model.data')

        template_id = imd_obj.get_object_reference(
            cursor, uid,
            'somre_giscere_oferta',
            'omie_representacio_mail_template'
        )[1]

        ctx = context.copy()
        ctx.update({
            'today': datetime.now().strftime('%Y-%m-%d'),
            'all_ok': len(errors) == 0,
            'resultat': 'OK' if len(errors) == 0 else 'ERRORS',
            'info': info,
            'errors': errors,
            'energia': energia
        })

        self.pool.get('poweremail.templates').generate_mail(
            cursor, uid, template_id, [1], context=ctx)

    def _cron_giscere_daily_offer(self, cursor, uid, context=None):  # noqa: C901
        """
        CREATE a daily offer for day D+1 for each Offer Unit
        :param cursor: OpenERP DB cursor
        :param uid: OpenERP User ID
        :param context: OpenERP Current Context
        :return: True
        """
        if context is None:
            context = {}

        unitat_obj = self.pool.get('giscere.unitat.oferta')
        oferta_obj = self.pool.get('giscere.oferta')
        omie_oferta_obj = self.pool.get('giscedata.omie.oferta')
        conf_obj = self.pool.get('res.config')

        logger = logging.getLogger('openerp.{}'.format(__name__))
        logger.info('Generating GISCERE Daily Offer...')

        # Obtenir el nombre de dies a futur per a generar i publicar oferta
        n_days = literal_eval(conf_obj.get(cursor, uid, 'representacio_auto_oferta_n_days', '1'))
        auto_generate_omie = literal_eval(conf_obj.get(
            cursor, uid, 'representacio_auto_generar_oferta_omie', '0'))
        auto_publish_omie = literal_eval(conf_obj.get(
            cursor, uid, 'representacio_auto_publicar_oferta_omie', '0'))
        auto_mail_notify = literal_eval(conf_obj.get(
            cursor, uid, 'representacio_auto_omie_mail_notification', '0'))
        data_inici_previsions_qh = conf_obj.get(cursor, uid,
                                                'giscere_oferta_utilitzar_previsions_qh',
                                                '2025-10-01')

        info = []
        energia = []
        errors = []
        now = datetime.now()
        for d in range(n_days):
            data_oferta = (now + timedelta(days=d + 1)).strftime('%Y-%m-%d')

            # For each unit active on date
            unitats = unitat_obj.search(cursor, uid, [('data_alta', '<=', data_oferta),
                                                      '|',
                                                      ('data_baixa', '>=', data_oferta),
                                                      ('data_baixa', '=', False)
                                                      ], context={'active_test': False})

            for unitat in unitats:
                unitat_oferta = unitat_obj.read(cursor, uid, unitat, ['name'])['name']
                try:
                    # Generem l'Oferta de Representació
                    wiz_vals = {'data_oferta': data_oferta, 'unitat_oferta': unitat}
                    if data_oferta >= data_inici_previsions_qh:
                        wiz_vals.update({'qh_forecast': True, 'use_qh_forecasts': True})
                    wiz_id = self.create(cursor, uid, wiz_vals)
                    wiz_oferta = self.simple_browse(cursor, uid, wiz_id, context=context)
                    oferta_id = wiz_oferta.action_generar()
                    if oferta_id:
                        msg = "S'ha creat l'oferta diària amb ID {} per la Unitat d'Oferta {} pel día {}".format(  # noqa: E501
                            oferta_id, unitat_oferta, data_oferta
                        )
                        logger.info(msg)

                        # Marquem com a publicada l'Oferta de Representació
                        res = oferta_obj.publicar(cursor, uid, [oferta_id], context=context)
                        if res:
                            msg = "S'ha marcat com a publicada l'oferta diària amb ID {} per la Unitat d'Oferta {} pel día {}".format(  # noqa: E501
                                oferta_id, unitat_oferta, data_oferta
                            )
                            logger.info(msg)

                            # Creem l'Oferta d'OMIE
                            if auto_generate_omie:
                                oferta_obj.crear_oferta(cursor, uid, [oferta_id], context=context)
                                oferta_data = oferta_obj.read(cursor, uid, oferta_id, [
                                                              'oferta_a_omie', 'oferta_omie_id'])
                                if oferta_data.get('oferta_a_omie', 'no_generada') == 'generada':
                                    msg = "S'ha generat oferta d'OMIE per la Unitat d'Oferta {} pel día {}".format(  # noqa: E501, F523
                                        oferta_id, unitat_oferta, data_oferta
                                    )
                                    logger.info(msg)

                                    # Publiquem l'Oferta a OMIE
                                    if auto_publish_omie:
                                        omie_oferta_id = oferta_data.get('oferta_omie_id')
                                        omie_oferta_id = int(omie_oferta_id.split(',')[1])
                                        for attempt in range(1, MAX_RETRIES + 1):
                                            try:
                                                omie_oferta_obj.enviar_oferta(
                                                    cursor, uid, [omie_oferta_id], context=context)
                                                break
                                            except Exception as e:
                                                if attempt == MAX_RETRIES:
                                                    raise
                                                sleep_time = attempt * 3
                                                time.sleep(sleep_time)
                                        oferta_new_state = oferta_obj.read(
                                            cursor, uid, oferta_id, ['oferta_a_omie'])
                                        if oferta_new_state.get('oferta_a_omie', 'generada') == 'enviada':  # noqa: E501
                                            msg = "L'oferta d'OMIE per la Unitat d'Oferta {} pel día {} ha estat acceptada.".format(  # noqa: E501
                                                unitat_oferta, data_oferta
                                            )
                                            logger.info(msg)
                                            read_vals = ['texto_respuesta',
                                                         'id_unidad', 'total_energia']
                                            omie_data = omie_oferta_obj.read(
                                                cursor, uid, omie_oferta_id, read_vals)
                                            res_omie = omie_data['texto_respuesta'].split('\n')[0]
                                            info.append(res_omie)
                                            ener = '{}: {} MWh pel dia {}.'.format(
                                                omie_data['id_unidad'], omie_data['total_energia'], data_oferta  # noqa: E501
                                            )
                                            energia.append(ener)
                                        elif oferta_new_state.get('oferta_a_omie', 'generada') == 'enviada_error':  # noqa: E501
                                            msg = "L'oferta d'OMIE per la Unitat d'Oferta {} pel día {} ha retornat error.".format(  # noqa: E501
                                                unitat_oferta, data_oferta
                                            )
                                            logger.info(msg)
                                            errors.append(msg)
                                        else:
                                            msg = "L'oferta d'OMIE per la Unitat d'Oferta {} pel día {} no s'ha enviat.".format(  # noqa: E501
                                                unitat_oferta, data_oferta
                                            )
                                            logger.info(msg)
                                            errors.append(msg)

                                else:
                                    msg = "No s'ha generat oferta d'OMIE per l'oferta diària amb ID {} per la Unitat d'Oferta {} pel día {}".format(  # noqa: E501
                                        oferta_id, unitat_oferta, data_oferta
                                    )
                                    logger.info(msg)
                                    errors.append(msg)

                        else:
                            msg = "No s'ha marcat com a publicada l'oferta diària amb ID {} per la Unitat d'Oferta {} pel día {}".format(  # noqa: E501
                                oferta_id, unitat_oferta, data_oferta
                            )
                            logger.info(msg)
                            errors.append(msg)

                    else:
                        error_msg = "No s'ha pogut crear ni publicar l'oferta diària de la Unitat d'Oferta {} pel día {}.".format(  # noqa: E501
                            unitat_oferta, data_oferta
                        )
                        logger.error(error_msg)
                        errors.append(error_msg)
                except Exception as e:
                    error_msg = "No s'ha pogut crear ni publicar l'oferta diària de la Unitat d'Oferta {} pel día {}: {}".format(  # noqa: E501
                        unitat_oferta, data_oferta, e
                    )
                    logger.error(error_msg)
                    errors.append(error_msg)

        # Enviament d'e-mail amb els resultats
        if auto_mail_notify:
            self.send_email(cursor, uid, info, errors, energia, context=context)

        return True


WizardGisceReGenerarOfertaSom()
