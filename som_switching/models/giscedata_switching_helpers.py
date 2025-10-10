# -*- coding: utf-8 -*-
from osv import osv
from datetime import datetime, timedelta
from tools.translate import _

# from som_gurb.models.giscedata_switching import _contract_has_gurb_category


class GiscedataSwitchingHelpers(osv.osv):

    _name = "giscedata.switching.helpers"
    _inherit = "giscedata.switching.helpers"

    def activar_polissa_from_m1_canvi_titular_subrogacio(self, cursor, uid, sw_id, old_polissa=None, context=None):  # noqa: E501
        res = super(
            GiscedataSwitchingHelpers, self
        ).activar_polissa_from_m1_canvi_titular_subrogacio(
            cursor, uid, sw_id, old_polissa=old_polissa, context=context)

        sw_obj = self.pool.get("giscedata.switching")
        payment_mode_o = self.pool.get("payment.mode")
        payment_mode_id = payment_mode_o.search(cursor, uid, [("name", "=", "ENGINYERS")])
        sw = sw_obj.browse(cursor, uid, sw_id, context=context)
        sw.cups_polissa_id.write({"payment_mode_id": payment_mode_id[0]})

        return res

    def ct_baixa_mailchimp(self, cursor, uid, sw_id, context=None):
        sw_obj = self.pool.get("giscedata.switching")
        m101_obj = self.pool.get("giscedata.switching.m1.01")
        conf_obj = self.pool.get("res.config")
        pol_obj = self.pool.get("giscedata.polissa")

        sw = sw_obj.browse(cursor, uid, sw_id)
        pas_actual = sw.get_pas()
        use_new_contract = bool(
            int(conf_obj.get(cursor, uid, "sw_m1_owner_change_subrogacio_new_contract", "1"))
        )

        step_name = sw.step_id.name
        if not sw.finalitzat:
            info = _(
                u"[Baixa Mailchimp] Com que el cas (M1-%s) no està finalitzat "
                u"no s'ha donat de baixa l'antic titular."
            ) % (step_name)
            return (_(u"OK"), info)

        if sw.rebuig or step_name == "04":
            info = _(
                u"[Baixa Mailchimp] Aquest cas (M1-%s) està finalitzat però és un "
                u"rebuig. No es dona de baixa l'antic titular."
            ) % (step_name)
            return (_(u"OK"), info)

        pas01_info = m101_obj.read(
            cursor,
            uid,
            m101_obj.search(cursor, uid, [("sw_id", "=", sw_id)])[0],
            ["sollicitudadm", "canvi_titular"],
        )

        if pas01_info["sollicitudadm"] not in ("S", "A") or pas01_info["canvi_titular"] not in (
            "S",
            "T",
        ):
            info = _(u"[Baixa Mailchimp] Aquest cas (M1-%s) no és d'un canvi de titular.") % (
                step_name
            )
            return (_(u"OK"), info)
        elif pas01_info["canvi_titular"] == "S" and not use_new_contract:
            # si es subrogació sense nou contracte, mirem que el titular abans i
            # després de la data d'activació són diferents
            model_name = sw.get_pas_model_name()
            # 'giscedata.switching.m1.02' or 'giscedata.switching.m1.05' expected
            m10X_obj = self.pool.get(model_name)

            data_activacio = m10X_obj.read(cursor, uid, pas_actual.id, ["data_activacio"])[
                "data_activacio"
            ]
            data_activacio = datetime.strptime(data_activacio, "%Y-%m-%d")
            data_previa = datetime.strftime(data_activacio - timedelta(days=1), "%Y-%m-%d")

            old_titular_id = pol_obj.read(
                cursor, uid, sw.cups_polissa_id.id, ["titular"], context={"date": data_previa}
            )["titular"][0]
            actual_titular_id = sw.titular_polissa.id

            if old_titular_id == actual_titular_id:
                info = _(
                    u"[Baixa Mailchimp] El canvi pel cas (M1-%s) encara no "
                    u"s'ha activat. No es dona de baixa l'antic titular."
                ) % (step_name)
                return (_(u"OK"), info)
        elif (
            pas01_info["canvi_titular"] == "T" or use_new_contract
        ) and not sw.polissa_ref_id.active:
            # encara no s'ha activat el canvi
            info = _(
                u"[Baixa Mailchimp] El canvi pel cas (M1-%s) encara no "
                u"s'ha activat. No es dona de baixa l'antic titular."
            ) % (step_name)
            return (_(u"OK"), info)
        else:
            old_titular_id = sw.cups_polissa_id.titular.id

        return self._check_and_archive_old_owner(cursor, uid, old_titular_id)

    def cn06_bn05_baixa_mailchimp(self, cursor, uid, sw_id, context=None):
        sw_obj = self.pool.get("giscedata.switching")
        sw = sw_obj.browse(cursor, uid, sw_id)

        step_name = sw.step_id.name
        if not sw.finalitzat:
            info = _(
                u"[Baixa Mailchimp] Com que el cas (%s-%s) no està finalitzat "
                u"no s'ha donat de baixa l'antic titular."
            ) % (sw.proces_id.name, step_name)
            return (_(u"OK"), info)

        is_cn06 = step_name == "06" and sw.proces_id.name in ["C1", "C2"]
        is_bn05 = step_name == "05" and sw.proces_id.name in ["B1", "B2"]
        if not (is_cn06 or is_bn05):
            info = _(u"[Baixa Mailchimp] Aquest cas (%s-%s) no és un Cn-06 ni Bn-05.") % (
                sw.proces_id.name,
                step_name,
            )
            return (_(u"OK"), info)

        if sw.cups_polissa_id.active:
            info = _(
                u"[Baixa Mailchimp] No s'ha donat de baixa el titular perquè la pòlissa està activa."  # noqa: E501
            )
            return (_(u"OK"), info)

        titular_id = sw.cups_polissa_id.titular.id
        return self._check_and_archive_old_owner(cursor, uid, titular_id)

    def _check_and_archive_old_owner(self, cursor, uid, titular_id, context=None):
        pol_obj = self.pool.get("giscedata.polissa")

        pol_actives = pol_obj.search(
            cursor, uid, [("titular", "=", titular_id)]
        )  # per defecte només busca les actives
        if pol_actives:
            info = _(
                u"[Baixa Mailchimp] No s'ha iniciat el procés de baixa "
                u"perque l'antic titular encara té pòlisses associades."
            )

            return "OK", info

        partner_obj = self.pool.get("res.partner.address")
        partner_obj.unsubscribe_partner_in_customers_no_members_lists(cursor, uid, titular_id)

        info = _(
            u"[Baixa Mailchimp] S'ha iniciat el procés de baixa " u"per l'antic titular (ID %d)"
        ) % (titular_id)

        return "OK", info

    def activa_cac_r1_02_rebuig(self, cursor, uid, sw_id, context=None):
        res = super(GiscedataSwitchingHelpers, self).activa_cac_r1_02_rebuig(
            cursor, uid, sw_id, context=context
        )
        sw_obj = self.pool.get("giscedata.switching")
        atc_o = self.pool.get("giscedata.atc")
        sw = sw_obj.browse(cursor, uid, sw_id)
        cac = None
        if sw.ref and sw.ref.split(",")[0] == "giscedata.atc":
            cac = atc_o.browse(cursor, uid, int(sw.ref.split(",")[1]), context=context)
        elif sw.ref2 and sw.ref2.split(",")[0] == "giscedata.atc":
            cac = atc_o.browse(cursor, uid, int(sw.ref2.split(",")[1]), context=context)
        if (
            cac
            and cac.state not in ["done", "cancel"]
            and cac.tancar_cac_al_finalitzar_r1
            and len(res) > 1
            and res[0].upper() == "OK"
        ):
            cac.case_log()
            cac.write({"description": _(u"Cas tancat automaticament al importar R1-02.")})
            cac.case_log()
            cac.case_close(context)
        return res

    def m105_acord_repartiment_autoconsum(self, cursor, uid, sw_id, context=None):
        sw_obj = self.pool.get('giscedata.switching')
        polissa_obj = self.pool.get('giscedata.polissa')
        info = ''

        sw = sw_obj.browse(cursor, uid, sw_id, context=context)
        polissa = polissa_obj.browse(
            cursor, uid, sw.cups_polissa_id.id, context={'prefetch': False}
        )

        # tanquem el cas
        if not sw.case_close():
            info += _(
                u"Per la pólissa '%s' no hem pogut tancar el cas %s") % (polissa.name, sw.name)
            return _(u'ERROR'), info
        else:
            info += _(u"  * S'ha tancat correctament.")
            return 'OK', info


GiscedataSwitchingHelpers()
