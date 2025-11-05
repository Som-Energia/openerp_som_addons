# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from datetime import datetime


class GiscedataAtcTag(osv.osv):
    _name = "giscedata.atc.tag"

    _columns = {
        "name": fields.char(u"Etiqueta", size=100),
        "titol": fields.char(u"Títol", size=200),
        "description": fields.char(u"Descripció", size=300),
        "creation_date": fields.date(u"Data creació", required=True),
        "text_R1": fields.text(u"Proposta text R1"),
        "active": fields.boolean("Actiu"),
    }

    _defaults = {
        "active": lambda *a: True,
        "creation_date": lambda *a: datetime.today().strftime("%Y-%m-%d"),
    }


GiscedataAtcTag()


class GiscedataAtc(osv.osv):

    _inherit = "giscedata.atc"

    def case_close_pre_hook(self, cursor, uid, ids, *args):
        if len(args):
            context = args[0]
        else:
            context = {}

        res = super(GiscedataAtc, self).case_close_pre_hook(cursor, uid, ids, *args)

        conf_obj = self.pool.get("res.config")
        treure = int(conf_obj.get(cursor, uid, "treure_facturacio_suspesa_on_cac_close", "0"))
        if treure:
            pol_ids = self.read(cursor, uid, ids, ["polissa_id"], context=context)
            pol_ids = [x["polissa_id"][0] for x in pol_ids]
            self.pool.get("giscedata.polissa").write(
                cursor, uid, pol_ids, {"facturacio_suspesa": False}
            )
        return res

    def unlink(self, cursor, uid, ids, context=None):
        return self.case_cancel(cursor, uid, ids, context)

    def case_cancel(self, cursor, uid, ids, *args):
        r101_obj = self.pool.get("giscedata.switching")
        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        self.case_cancel_this(cursor, uid, ids, *args)

        cancel_r1_ids = []
        for atc in self.browse(cursor, uid, ids):
            ref = atc.ref if atc.ref else atc.ref2
            if ref and 'giscedata.switching,' in ref:
                cancel_r1_ids.append(int(ref.split(',')[1]))

        if cancel_r1_ids:
            r101_obj.case_cancel(cursor, uid, cancel_r1_ids, *args)
        return True

    def case_cancel_this(self, cursor, uid, ids, *args):  # noqa: C901
        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        cancel_ids = []
        for atc_id in ids:
            atc = self.browse(cursor, uid, atc_id)

            r1 = atc.has_process
            if r1:
                ref = atc.ref if atc.ref else atc.ref2
                model, index = ref.split(",")
                m_obj = self.pool.get(model)
                r1 = m_obj.browse(cursor, uid, int(index))

            if (
                atc.state == "pending"
                and atc.process_step == "01"
                and r1
                and r1.enviament_pendent is False
            ):
                raise osv.except_osv(
                    _(u"Warning"),
                    _(
                        u"Cas ATC {} no es pot cancel·lar: R1 01 està pendent del pas finalitzador"
                    ).format(atc_id),
                )

            if atc.state in ["open", "pending"] and atc.process_step == "02":
                r1_finalitzat = self.has_r1_no_finalitzat(cursor, uid, atc_id)
                if r1 and not r1_finalitzat:
                    raise osv.except_osv(
                        _(u"Warning"),
                        _(
                            u"Cas ATC {} no es pot cancel·lar: R1 02 l'heu de revisar i tancar"
                        ).format(atc_id),
                    )

                if r1 and r1_finalitzat:
                    raise osv.except_osv(
                        _(u"Warning"),
                        _(
                            u"Cas ATC {} no es pot cancel·lar: R1 02 està pendent del pas finalitzador"  # noqa: E501
                        ).format(atc_id),
                    )

            if atc.state == "open" and atc.process_step == "03":
                raise osv.except_osv(
                    _(u"Warning"),
                    _(u"Cas ATC {} no es pot cancel·lar: R1 03 en estat Obert").format(atc_id),
                )

            if atc.state == "pending" and atc.process_step == "03":
                raise osv.except_osv(
                    _(u"Warning"),
                    _(
                        u"Cas ATC {} no es pot cancel·lar: R1 03 està pendent del pas finalitzador"
                    ).format(atc_id),
                )

            if atc.state == "open" and atc.process_step == "04":
                raise osv.except_osv(
                    _(u"Warning"),
                    _(
                        u"Cas ATC {} no es pot cancel·lar: R1 04 en estat Obert - ERROR MANUAL -"
                    ).format(atc_id),
                )

            if atc.state == "pending" and atc.process_step == "04":
                raise osv.except_osv(
                    _(u"Warning"),
                    _(u"Cas ATC {} no es pot cancel·lar: R1 04 en estat Pendent").format(atc_id),
                )

            if atc.state == "open" and atc.process_step == "05":
                if r1 and r1.state != "open":
                    raise osv.except_osv(
                        _(u"Warning"),
                        _(
                            u"Cas ATC {} no es pot cancel·lar: R1 05 l'heu de revisar i tancar - Error manual R1 no oberta"  # noqa: E501
                        ).format(atc_id),
                    )
                else:
                    raise osv.except_osv(
                        _(u"Warning"),
                        _(
                            u"Cas ATC {} no es pot cancel·lar: R1 05 l'heu de revisar i tancar"
                        ).format(atc_id),
                    )

            if atc.state in ["open", "pending"] and atc.process_step == "08":
                raise osv.except_osv(
                    _(u"Warning"),
                    _(
                        u"Cas ATC {} no es pot cancel·lar: R1 08 no pots cancel·lar una cancel·lació, cal esperar a rebre pas 09 de distribuïdora"  # noqa: E501
                    ).format(atc_id),
                )

            if atc.state == "open" and atc.process_step == "09":
                if r1 and r1.rebuig:
                    raise osv.except_osv(
                        _(u"Warning"),
                        _(
                            u"Cas ATC {} no es pot cancel·lar: R1 09 de rebuig no es pot cancel·lar ni tancar"  # noqa: E501
                        ).format(atc_id),
                    )
                else:
                    raise osv.except_osv(
                        _(u"Warning"),
                        _(
                            u"Cas ATC {} no es pot cancel·lar: R1 09 d'acceptació s'ha de tancar i no cancel·lar"  # noqa: E501
                        ).format(atc_id),
                    )

            if atc.state not in ("draft", "pending", "open"):
                raise osv.except_osv(
                    _(u"Warning"),
                    _(
                        u"Cas ATC {} no es pot cancel·lar: L'estat no és Pendent, Esborrany o Obert"
                    ).format(atc_id),
                )

            cancel_ids.append(atc_id)

        if cancel_ids:
            return super(GiscedataAtc, self).case_cancel(cursor, uid, cancel_ids, *args)

        return True

    _columns = {
        "tag": fields.many2one("giscedata.atc.tag", "Etiqueta"),
    }


GiscedataAtc()
