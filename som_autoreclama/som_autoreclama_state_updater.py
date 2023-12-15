# -*- coding: utf-8 -*-
from osv import osv
from tqdm import tqdm
from tools.translate import _
from tools import email_send


class SomAutoreclamaStateUpdater(osv.osv_memory):

    _name = "som.autoreclama.state.updater"

    def get_atc_candidates_to_update(self, cursor, uid, context=None):
        atc_obj = self.pool.get("giscedata.atc")
        search_params = [
            ("active", "=", True),
            ("state", "=", "pending"),
            ("agent_actual", "=", "10"),  # Distri
            ("autoreclama_state.is_last", "=", False),
        ]
        return atc_obj.search(cursor, uid, search_params)

    def get_autoreclama_state_name(self, cursor, uid, item_id, namespace, context=None):
        item_obj = self.pool.get("giscedata." + namespace)
        data = item_obj.read(cursor, uid, item_id, ["autoreclama_state"], context=context)
        if (
            "autoreclama_state" in data
            and data["autoreclama_state"]
            and len(data["autoreclama_state"]) > 1
        ):
            return data["autoreclama_state"][1]
        return "No initial state"

    def update_atcs_if_possible(self, cursor, uid, ids, context=None):
        updated = []
        not_updated = []
        errors = []
        msg = _("Accions casos ATC\n")

        for atc_id in tqdm(ids):
            actual_state = self.get_autoreclama_state_name(cursor, uid, atc_id, "atc", context)
            result, message = self.update_atc_if_possible(cursor, uid, atc_id, context)
            if result:
                updated.append(atc_id)
                next_state = self.get_autoreclama_state_name(cursor, uid, atc_id, "atc", context)
                msg += _("Cas ATC amb id {} ha canviat d'estat: {} --> {}\n").format(
                    atc_id, actual_state, next_state
                )
                msg += _(" - {}\n").format(message)
            elif result is False:
                not_updated.append(atc_id)
                msg += _("Cas ATC amb id {} no li toca canviar d'estat, estat actual: {}\n").format(
                    atc_id, actual_state
                )
                msg += _(" - {}\n").format(message)
            else:
                errors.append(atc_id)
                msg += _(
                    "Cas ATC amb id {} no ha canviat d'estat per error, estat actual: {}\n"
                ).format(atc_id, actual_state)
                msg += _(" - {}\n").format(message)


        summary = _("Sumari casos ATC\n")
        summary += _("casos ATC que han canviat d'estat: .................. {}\n".format(len(updated)))
        summary += _(
            "casos ATC que no han canviat d'estat: ............... {}\n".format(len(not_updated))
        )
        summary += _("casos ATC que no han pogut canviar per un error: .... {}\n".format(len(errors)))
        summary += _("\n")

        if updated:
            summary += _("Id's de casos ATC que han canviat d'estat\n")
            summary += ",".join(str(upd) for upd in updated)
            summary += _("\n\n")

        if errors:
            summary += _("Id's de casos ATC que han donat error (REVISAR)\n")
            summary += ",".join(str(error) for error in errors)
            summary += _("\n\n")

        return updated, not_updated, errors, msg, summary

    def update_atc_if_possible(self, cursor, uid, atc_id, context=None):
        atc_obj = self.pool.get("giscedata.atc")
        history_obj = self.pool.get("som.autoreclama.state.history.atc")
        state_obj = self.pool.get("som.autoreclama.state")
        cond_obj = self.pool.get("som.autoreclama.state.condition")
        atc_data = atc_obj.get_autoreclama_data(cursor, uid, atc_id, context)

        state = atc_obj.read(cursor, uid, atc_id, ["autoreclama_state"], context)
        if "autoreclama_state" in state and state["autoreclama_state"]:
            autoreclama_state_id = state["autoreclama_state"][0]
        else:
            return False, _(u"Sense estat d'autoreclama inicial")

        cond_ids = cond_obj.search(
            cursor,
            uid,
            [
                ("state_id", "=", autoreclama_state_id),
                ("active", "=", True),
            ],
            order="priority",
            context=context,
        )

        do_not_execute = context and context.get("search_only", False)
        for cond_id in cond_ids:
            if cond_obj.fit_atc_condition(cursor, uid, cond_id, atc_data):
                if do_not_execute:
                    return True, _(u"Testing")

                next_state_id = cond_obj.read(
                    cursor, uid, cond_id, ["next_state_id"], context=context
                )["next_state_id"][0]
                action_result = state_obj.do_action(cursor, uid, next_state_id, atc_id, "atc", context)
                if action_result["do_change"]:
                    history_obj.historize(
                        cursor,
                        uid,
                        atc_id,
                        next_state_id,
                        None,
                        action_result.get("created_atc", False),
                        context,
                    )
                    return True, action_result.get("message", "No message!!")
                else:
                    return None, action_result.get("message", "No message!!")

        return False, _(u"No compleix cap condició activa, examinades {} condicions.").format(
            len(cond_ids)
        )

    def get_polissa_candidates_to_update(self, cursor, uid, context=None):
        pol_obj = self.pool.get("giscedata.polissa")
        search_params = [
            ("active", "=", True),
            ("state", "=", "TODO"),
            ("autoreclama_state.is_last", "=", False),
        ]
        return pol_obj.search(cursor, uid, search_params)

    def update_polisses_if_possible(self, cursor, uid, ids, context=None):
        updated = []
        not_updated = []
        errors = []
        msg = _("Accions pòlisses\n")

        for polissa_id in tqdm(ids):
            actual_state = self.get_autoreclama_state_name(cursor, uid, polissa_id, "polissa", context)
            result, message = self.update_polissa_if_possible(cursor, uid, polissa_id, context)
            if result:
                updated.append(polissa_id)
                next_state = self.get_autoreclama_state_name(cursor, uid, polissa_id, "polissa", context)
                msg += _("Pòlissa amb id {} ha canviat d'estat: {} --> {}\n").format(
                    polissa_id, actual_state, next_state
                )
                msg += _(" - {}\n").format(message)
            elif result is False:
                not_updated.append(polissa_id)
                msg += _("Pòlissa amb id {} no li toca canviar d'estat, estat actual: {}\n").format(
                    polissa_id, actual_state
                )
                msg += _(" - {}\n").format(message)
            else:
                errors.append(polissa_id)
                msg += _(
                    "Pòlissa amb id {} no ha canviat d'estat per error, estat actual: {}\n"
                ).format(polissa_id, actual_state)
                msg += _(" - {}\n").format(message)


        summary = _("Sumari pòlisses\n")
        summary += _("pòlisses que han canviat d'estat: .................. {}\n".format(len(updated)))
        summary += _(
            "pòlisses que no han canviat d'estat: ............... {}\n".format(len(not_updated))
        )
        summary += _("pòlisses que no han pogut canviar per un error: .... {}\n".format(len(errors)))
        summary += _("\n")

        if updated:
            summary += _("Id's de pòlisses que han canviat d'estat\n")
            summary += ",".join(str(upd) for upd in updated)
            summary += _("\n\n")

        if errors:
            summary += _("Id's de pòlisses que han donat error (REVISAR)\n")
            summary += ",".join(str(error) for error in errors)
            summary += _("\n\n")

        return updated, not_updated, errors, msg, summary

    def update_polissa_if_possible(self, cursor, uid, polissa_id, context=None):
        polissa_obj = self.pool.get("giscedata.polissa")
        history_obj = self.pool.get("som.autoreclama.state.history.polissa")
        state_obj = self.pool.get("som.autoreclama.state")
        cond_obj = self.pool.get("som.autoreclama.state.condition")
        polissa_data = polissa_obj.get_autoreclama_data(cursor, uid, polissa_id, context)

        state = polissa_obj.read(cursor, uid, polissa_id, ["autoreclama_state"], context)
        if "autoreclama_state" in state and state["autoreclama_state"]:
            autoreclama_state_id = state["autoreclama_state"][0]
        else:
            return False, _(u"Sense estat d'autoreclama inicial")

        cond_ids = cond_obj.search(
            cursor,
            uid,
            [
                ("state_id", "=", autoreclama_state_id),
                ("active", "=", True),
            ],
            order="priority",
            context=context,
        )

        do_not_execute = context and context.get("search_only", False)
        for cond_id in cond_ids:
            if cond_obj.fit_polissa_condition(cursor, uid, cond_id, polissa_data):
                if do_not_execute:
                    return True, _(u"Testing")

                next_state_id = cond_obj.read(
                    cursor, uid, cond_id, ["next_state_id"], context=context
                )["next_state_id"][0]
                action_result = state_obj.do_action(cursor, uid, next_state_id, polissa_id, 'polissa', context)
                if action_result["do_change"]:
                    history_obj.historize(
                        cursor,
                        uid,
                        polissa_id,
                        next_state_id,
                        None,
                        action_result.get("created_atc", False),
                        context,
                    )
                    return True, action_result.get("message", "No message!!")
                else:
                    return None, action_result.get("message", "No message!!")

        return False, _(u"No compleix cap condició activa, examinades {} condicions.").format(
            len(cond_ids)
        )

    def state_updater(self, cursor, uid, context=None):
        atc_ids = self.get_atc_candidates_to_update(cursor, uid, context)
        c, b, c, atc_msg, atc_sum = self.update_atcs_if_possible(cursor, uid, atc_ids, context)

        pol_ids = self.get_polissa_candidates_to_update(cursor, uid, context)
        a, b, c, pol_msg, pol_sum =self.update_polisses_if_possible(cursor, uid, pol_ids, context)

        return "\n\n".join([atc_sum, pol_sum, atc_msg, pol_msg])

    def _cronjob_state_updater_mail_text(self, cursor, uid, data=None, context=None):
        if not data:
            data = {}
        if not context:
            context = {}

        subject = _(u"Resultat accions batch d'autoreclama")
        msg = self.state_updater(cursor, uid, context)

        emails_to = filter(lambda a: bool(a), map(str.strip, data.get("emails_to", "").split(",")))
        if emails_to:
            user_obj = self.pool.get("res.users")
            email_from = user_obj.browse(cursor, uid, uid).address_id.email
            email_send(email_from, emails_to, subject, msg)

        return True


SomAutoreclamaStateUpdater()
