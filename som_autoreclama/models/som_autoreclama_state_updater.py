# -*- coding: utf-8 -*-
from osv import osv
from tqdm import tqdm
from tools.translate import _
from tools import email_send


_namespaces = {
    'atc': {
        'model': 'giscedata.atc',
        'history_model': 'som.autoreclama.state.history.atc',
        'state_field': 'autoreclama_state',
        'name': _('Cas ATC'),
        'block_name': _('Casos ATC 029'),
    },
    'polissa': {
        'model': 'giscedata.polissa',
        'history_model': 'som.autoreclama.state.history.polissa',
        'state_field': 'autoreclama_state',
        'name': _('Pòlissa'),
        'block_name': _('Pòlisses ATC 006'),
    },
    'polissa009': {
        'model': 'giscedata.polissa',
        'history_model': 'som.autoreclama.state.history.polissa009',
        'state_field': 'autoreclama_state009',
        'name': _('Pòlissa'),
        'block_name': _('Pòlisses ATC 009'),
    },
}


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
        item_obj = self.pool.get(_namespaces[namespace]['model'])
        autoreclama_state = _namespaces[namespace]['state_field']
        data = item_obj.read(cursor, uid, item_id, [autoreclama_state], context=context)
        if (
            autoreclama_state in data
            and data[autoreclama_state]
            and len(data[autoreclama_state]) > 1
        ):
            return data[autoreclama_state][0], data[autoreclama_state][1]
        return None, "No initial state"

    def get_polissa_candidates_to_update(self, cursor, uid, namespace, context=None):
        pol_obj = self.pool.get("giscedata.polissa")
        autoreclama_state = _namespaces[namespace]['state_field']
        search_params = [
            ("state", "in", ['activa', 'baixa', 'impagament', 'modcontractual']),
            (autoreclama_state + ".is_last", "=", False),
        ]
        return pol_obj.search(cursor, uid, search_params, context={"active_test": False})

    def get_item_name(self, cursor, uid, item_id, namespace, context=None):
        if namespace == 'atc':
            return item_id

        pol_obj = self.pool.get('giscedata.polissa')
        pol_data = pol_obj.read(cursor, uid, item_id, ['name'], context=context)
        return "{} - {}".format(item_id, pol_data['name'])

    def get_names(self, cursor, uid, item_ids, namespace, context=None):
        if namespace == 'atc':
            return item_ids

        pol_obj = self.pool.get('giscedata.polissa')
        pol_datas = pol_obj.read(cursor, uid, item_ids, ['name'], context=context)
        return [pol_data['name'] for pol_data in pol_datas]

    def get_review_states(self, cursor, uid, namespace):
        data_obj = self.pool.get("ir.model.data")
        review_state_id = data_obj.get_object_reference(
            cursor, uid, "som_autoreclama", "review_state_workflow_polissa"
        )[1]
        review_stat009_id = data_obj.get_object_reference(
            cursor, uid, "som_autoreclama", "review_state_workflow_polissa009"
        )[1]

        if namespace == 'atc':
            return []
        if namespace == 'polissa':
            return [review_state_id]
        if namespace == 'polissa009':
            return [review_stat009_id]
        return []

    def update_items_if_possible(self, cursor, uid, ids, namespace, verbose=True, context=None):
        cnd_obj = self.pool.get("som.autoreclama.state.condition")

        updated = []
        not_updated = []
        errors = []
        reviews = []
        review_states = self.get_review_states(cursor, uid, namespace)

        block_name = _namespaces[namespace]['block_name']
        msg = _("Accions {}\n").format(block_name)

        for item_id in tqdm(ids):
            actual_state_id, actual_state = self.get_autoreclama_state_name(
                cursor, uid, item_id, namespace, context)
            result, condition_id, message = self.update_item_if_possible(
                cursor, uid, item_id, namespace, context
            )
            item_name = self.get_item_name(cursor, uid, item_id, namespace, context)
            if result:
                updated.append(item_id)
                next_state_id, next_state = self.get_autoreclama_state_name(
                    cursor, uid, item_id, namespace, context)
                msg += _("{} amb id {} ha canviat d'estat: {} --> {} => condició {}\n").format(
                    _namespaces[namespace]['name'],
                    item_name, actual_state, next_state,
                    cnd_obj.get_string(cursor, uid, condition_id)
                )
                msg += _(" - {}\n").format(message)
                if next_state_id in review_states:
                    reviews.append(item_id)
            elif result is False:
                not_updated.append(item_id)
                if verbose:
                    msg += _("{} amb id {} no li toca canviar d'estat, estat actual: {}\n").format(
                        _namespaces[namespace]['name'], item_name, actual_state
                    )
                    msg += _(" - {}\n").format(message)
            else:
                errors.append(item_id)
                msg += _(
                    "{} amb id {} no ha canviat d'estat per error, estat actual: {} => condició {}\n"  # noqa: E501
                ).format(_namespaces[namespace]['name'], item_name, actual_state,
                         cnd_obj.get_string(cursor, uid, condition_id))
                msg += _(" - {}\n").format(message)

        summary = _("Sumari {}\n").format(block_name)
        summary += _("{} que han canviat d'estat: .................. {}\n".format(block_name, len(updated)))  # noqa: E501
        summary += _(
            "{} que no han canviat d'estat: ............... {}\n".format(block_name, len(not_updated))  # noqa: E501
        )
        summary += _("{} que no han pogut canviar per un error: .... {}\n".format(block_name, len(errors)))  # noqa: E501
        summary += _("\n")

        if updated:
            if namespace == 'atc':
                summary += _("Id's de {} que han canviat d'estat\n").format(block_name)
            else:
                summary += _("Número de les pòlisses que han canviat d'estat\n").format(block_name)
            updated_names = self.get_names(cursor, uid, updated, namespace, context)
            summary += ", ".join(str(upd) for upd in updated_names)
            summary += _("\n\n")

        if errors:
            if namespace == 'atc':
                summary += _("Id's de {} que han donat error (REVISAR)\n").format(block_name)
            else:
                summary += _("Número de les pòlisses que han donat error (REVISAR)\n").format(block_name)  # noqa: E501
            error_names = self.get_names(cursor, uid, errors, namespace, context)
            summary += ", ".join(str(error) for error in error_names)
            summary += _("\n\n")

        if reviews:
            if namespace == 'atc':
                summary += _("Id's de {} que han passat a estat 'Revisar'\n").format(block_name)
            else:
                summary += _("Número de les pòlisses que han passat a estat 'Revisar'\n").format(block_name)  # noqa: E501
            review_names = self.get_names(cursor, uid, reviews, namespace, context)
            summary += ", ".join(str(review) for review in review_names)
            summary += _("\n\n")

        return updated, not_updated, errors, msg, summary

    def update_item_if_possible(self, cursor, uid, item_id, namespace, context=None):
        if not context:
            context = {}

        item_obj = self.pool.get(_namespaces[namespace]['model'])
        history_obj = self.pool.get(_namespaces[namespace]['history_model'])
        state_obj = self.pool.get("som.autoreclama.state")
        cond_obj = self.pool.get("som.autoreclama.state.condition")
        cfg_obj = self.pool.get('res.config')
        context['days_ago_R1006'] = int(cfg_obj.get(
            cursor, uid, "som_autoreclama_2_006_in_a_row_days_ago", "120")
        )
        item_data = item_obj.get_autoreclama_data(cursor, uid, item_id, namespace, context)

        autoreclama_state = _namespaces[namespace]['state_field']
        state = item_obj.read(cursor, uid, item_id, [autoreclama_state], context)
        if autoreclama_state in state and state[autoreclama_state]:
            autoreclama_state_id = state[autoreclama_state][0]
        else:
            return False, None, _(u"Sense estat d'autoreclama inicial")

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
            if cond_obj.fit_condition(cursor, uid, cond_id, item_data, namespace):
                if do_not_execute:
                    return True, None, _(u"Testing")

                next_state_id = cond_obj.read(
                    cursor, uid, cond_id, ["next_state_id"], context=context
                )["next_state_id"][0]
                action_result = state_obj.do_action(
                    cursor, uid, next_state_id, item_id, namespace, context)
                if action_result["do_change"]:
                    history_obj.historize(
                        cursor,
                        uid,
                        item_id,
                        next_state_id,
                        None,
                        action_result.get("created_atc", False),
                        context,
                    )
                    return True, cond_id, action_result.get("message", "No message!!")
                else:
                    return None, cond_id, action_result.get("message", "No message!!")

        return False, None, _(u"No compleix cap condició activa, examinades {} condicions.").format(
            len(cond_ids)
        )

    def state_updater(self, cursor, uid, context=None):
        atc_ids = self.get_atc_candidates_to_update(cursor, uid, context)
        a, b, c, atc_msg, atc_sum = self.update_items_if_possible(
            cursor, uid, atc_ids, "atc", False, context)

        pol_ids = self.get_polissa_candidates_to_update(cursor, uid, "polissa", context)
        a, b, c, pol_msg, pol_sum = self.update_items_if_possible(
            cursor, uid, pol_ids, "polissa", False, context)

        pol_ids = self.get_polissa_candidates_to_update(cursor, uid, "polissa009", context)
        a, b, c, pol_msg, pol_sum = self.update_items_if_possible(
            cursor, uid, pol_ids, "polissa009", False, context)

        return "\n\n".join([atc_sum, pol_sum, atc_msg, pol_msg])

    def _cronjob_state_updater_mail_text(self, cursor, uid, data=None, context=None):
        if not data:
            data = {}
        if not context:
            context = {}

        subject = _(u"Resultat accions batch d'autoreclama")
        msg = self.state_updater(cursor, uid, context)
        emails_to = data.get("emails_to", "").split(",")
        emails = []
        for email_to in emails_to:
            if email_to:
                emails.append(email_to.strip())
        emails_to = emails

        if emails_to:
            user_obj = self.pool.get("res.users")
            email_from = user_obj.browse(cursor, uid, uid).address_id.email
            email_send(email_from, emails_to, subject, msg)

        return True


SomAutoreclamaStateUpdater()
