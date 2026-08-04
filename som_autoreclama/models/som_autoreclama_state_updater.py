# -*- coding: utf-8 -*-
from __future__ import absolute_import

from osv import osv
from tqdm import tqdm
from tools.translate import _
from tools import email_send
import json
import pooler

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

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
        'state_field': 'autoreclama009_state',
        'name': _('Pòlissa'),
        'block_name': _('Pòlisses ATC 009'),
    },
}


class SomAutoreclamaStateUpdater(osv.osv_memory):

    _name = "som.autoreclama.state.updater"

    def _rollback_cursor(self, cursor):
        if cursor:
            cursor.rollback()

    def _ensure_updater_config_context(self, cursor, uid, context=None):
        if context is None:
            context = {}

        cfg_obj = self.pool.get('res.config')
        if 'days_ago_R1006' not in context:
            context['days_ago_R1006'] = int(cfg_obj.get(
                cursor, uid, "som_autoreclama_2_006_in_a_row_days_ago", "120")
            )
        if 'days_ago_R1009' not in context:
            context['days_ago_R1009'] = int(cfg_obj.get(
                cursor, uid, "som_autoreclama_2_009_in_a_row_days_ago", "120")
            )
        return context

    def _get_condition_ids(self, cursor, uid, state_id, namespace, context=None):
        if not context:
            context = {}

        condition_cache = context.setdefault('_autoreclama_condition_cache', {})
        cache_key = state_id
        if cache_key not in condition_cache:
            cond_obj = self.pool.get("som.autoreclama.state.condition")
            condition_cache[cache_key] = cond_obj.search(
                cursor,
                uid,
                [
                    ("state_id", "=", state_id),
                    ("active", "=", True),
                ],
                order="priority",
                context=context,
            )
        return condition_cache[cache_key]

    def _get_condition_string(self, cursor, uid, condition_id, context=None):
        if not condition_id:
            return ""
        if not context:
            context = {}

        condition_string_cache = context.setdefault(
            '_autoreclama_condition_string_cache', {}
        )
        if condition_id not in condition_string_cache:
            cnd_obj = self.pool.get("som.autoreclama.state.condition")
            condition_string_cache[condition_id] = cnd_obj.get_string(
                cursor, uid, condition_id
            )
        return condition_string_cache[condition_id]

    def _get_condition_data(self, cursor, uid, condition_id, context=None):
        if not context:
            context = {}

        condition_data_cache = context.setdefault(
            '_autoreclama_condition_data_cache', {}
        )
        if condition_id not in condition_data_cache:
            cond_obj = self.pool.get("som.autoreclama.state.condition")
            condition_data_cache[condition_id] = cond_obj.read(
                cursor,
                uid,
                condition_id,
                ["days", "condition_code", "subtype_id", "next_state_id"],
                context=context,
            )
        return condition_data_cache[condition_id]

    def get_atc_candidates_to_update(self, cursor, uid, context=None):
        atc_obj = self.pool.get("giscedata.atc")
        search_params = [
            ("active", "=", True),
            ("state", "=", "pending"),
            ("agent_actual", "=", "10"),  # Distri
            ("autoreclama_state.is_last", "=", False),
        ]
        return atc_obj.search(cursor, uid, search_params, order="id")

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
        return pol_obj.search(
            cursor, uid, search_params, order="id", context={"active_test": False}
        )

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

    def get_names_as_link(self, cursor, uid, item_ids, namespace, title, context=None):
        if namespace == 'atc':
            url = self._generate_ATC_webclient_url_view(cursor, uid, item_ids, title, context)
        else:
            url = self._generate_polissa_webclient_url_view(cursor, uid, item_ids, title, context)

        return "<a href={}>obrir llista al client web</a>".format(url)

    def _generate_ATC_webclient_url_view(self, cursor, uid, item_ids, title, context=None):
        data_obj = self.pool.get("ir.model.data")
        tree_id = data_obj.get_object_reference(
            cursor, uid, "giscedata_atc", "giscedata_atc_tree-view"
        )[1]
        form_id = data_obj.get_object_reference(
            cursor, uid, "giscedata_atc", "giscedata_atc-view"
        )[1]
        action_id = data_obj.get_object_reference(
            cursor, uid, "giscedata_atc", "all_atc_case-act"
        )[1]
        model = 'giscedata.atc'
        return self._generate_webclient_url_view(
            cursor, uid, model, title, tree_id, form_id, action_id, item_ids, context=context
        )

    def _generate_polissa_webclient_url_view(self, cursor, uid, item_ids, title, context=None):
        data_obj = self.pool.get("ir.model.data")
        tree_id = data_obj.get_object_reference(
            cursor, uid, "giscedata_polissa", "view_polisses_tree"
        )[1]
        form_id = data_obj.get_object_reference(
            cursor, uid, "giscedata_polissa", "view_polisses_form"
        )[1]
        action_id = data_obj.get_object_reference(
            cursor, uid, "giscedata_polissa", "action_polisses"
        )[1]
        model = 'giscedata.polissa'
        return self._generate_webclient_url_view(
            cursor, uid, model, title, tree_id, form_id, action_id, item_ids, context=context
        )

    def _generate_webclient_url_view(self, cursor, uid, model, title, tree_id, form_id, action_id, item_ids, context=None):  # noqa: E501
        cfg_obj = self.pool.get('res.config')
        actions = {
            'model': model,
            'views': [[tree_id, "tree"], [form_id, "form"]],
            'title': title,
            'initialView': {'id': tree_id, 'type': 'tree'},
            'action_id': action_id,
            'action_type': 'ir.actions.act_window',
            'res_id': item_ids[0],
            'limit': 0,
            'searchParams': [['id', 'in', item_ids]],
            'actionRawData': {"context": "{'active_test': False}"}
        }

        actionj = {}
        for action in actions.items():
            if isinstance(action[1], (list, dict)):
                actionj[action[0]] = json.dumps(action[1])
            else:
                actionj[action[0]] = action[1]

        url_params = urlencode(actionj)
        base_url = cfg_obj.get(
            cursor, uid, "som_autoreclama_web_client_base_url", "https://somenergia.coop/")
        action = u'/action?'
        return u'{}{}{}'.format(base_url, action, url_params)

    def get_review_states(self, cursor, uid, namespace, context=None):
        if namespace == 'atc':
            return []

        if not context:
            context = {}

        review_states_cache = context.setdefault('_autoreclama_review_states_cache', {})
        if namespace in review_states_cache:
            return review_states_cache[namespace]

        data_obj = self.pool.get("ir.model.data")
        if namespace == 'polissa':
            semantic_id = "review_state_workflow_polissa"
        elif namespace == 'polissa009':
            semantic_id = "review_state_workflow_polissa009"
        else:
            review_states_cache[namespace] = []
            return []

        review_state_id = data_obj.get_object_reference(
            cursor, uid, "som_autoreclama", semantic_id
        )[1]
        review_states_cache[namespace] = [review_state_id]
        return review_states_cache[namespace]

    def update_items_if_possible(self, cursor, uid, ids, namespace, verbose=True, context=None):
        updated = []
        not_updated = []
        errors = []
        reviews = []
        review_states = self.get_review_states(cursor, uid, namespace, context)

        block_name = _namespaces[namespace]['block_name']
        msg = _("Accions {}\n").format(block_name)

        for item_id in tqdm(ids):
            new_cursor = None
            try:
                new_cursor = pooler.get_db(cursor.dbname).cursor()

                actual_state_id, actual_state = self.get_autoreclama_state_name(
                    new_cursor, uid, item_id, namespace, context
                )
                result, condition_id, message = self.update_item_if_possible(
                    new_cursor, uid, item_id, namespace, context
                )
                if result:
                    updated.append(item_id)
                    item_name = self.get_item_name(
                        new_cursor, uid, item_id, namespace, context
                    )
                    next_state_id, next_state = self.get_autoreclama_state_name(
                        new_cursor, uid, item_id, namespace, context
                    )
                    msg += _("{} amb id {} ha canviat d'estat: {} --> {} => condició {}\n").format(
                        _namespaces[namespace]['name'],
                        item_name,
                        actual_state,
                        next_state,
                        self._get_condition_string(new_cursor, uid, condition_id, context),
                    )
                    msg += _(" - {}\n").format(message)
                    if next_state_id in review_states:
                        reviews.append(item_id)
                elif result is False:
                    not_updated.append(item_id)
                    if verbose:
                        item_name = self.get_item_name(
                            new_cursor, uid, item_id, namespace, context
                        )
                        msg += _(
                            "{} amb id {} no li toca canviar d'estat, estat actual: {}\n"
                        ).format(_namespaces[namespace]['name'], item_name, actual_state)
                        msg += _(" - {}\n").format(message)
                else:
                    self._rollback_cursor(new_cursor)
                    errors.append(item_id)
                    item_name = self.get_item_name(
                        new_cursor, uid, item_id, namespace, context
                    )
                    msg += _(
                        "{} amb id {} no ha canviat d'estat per error, estat actual: {} => condició {}\n"  # noqa: E501
                    ).format(
                        _namespaces[namespace]['name'],
                        item_name,
                        actual_state,
                        self._get_condition_string(new_cursor, uid, condition_id, context),
                    )
                    msg += _(" - {}\n").format(message)
                    continue

                new_cursor.commit()
            except Exception as e:
                if new_cursor:
                    self._rollback_cursor(new_cursor)
                raise e
            finally:
                if new_cursor:
                    new_cursor.close()

        summary = _("Sumari {}\n").format(block_name)
        summary += _("{} que han canviat d'estat: .................. {}\n".format(block_name, len(updated)))  # noqa: E501
        summary += _("{} que no han canviat d'estat: ............... {}\n".format(block_name, len(not_updated)))  # noqa: E501
        summary += _("{} que no han pogut canviar per un error: .... {}\n".format(block_name, len(errors)))  # noqa: E501
        summary += _("\n")

        if updated:
            if namespace == 'atc':
                summary += _("Id's de {} que han canviat d'estat\n").format(block_name)
            else:
                summary += _("Número de les pòlisses que han canviat d'estat\n").format(block_name)
            updated_names = self.get_names(cursor, uid, updated, namespace, context)
            summary += ", ".join(str(upd) for upd in updated_names)
            summary += "  " + self.get_names_as_link(cursor, uid, updated, namespace, "Han canviat d'estat", context)  # noqa: E501
            summary += _("\n\n")

        if errors:
            if namespace == 'atc':
                summary += _("Id's de {} que han donat error (REVISAR)\n").format(block_name)
            else:
                summary += _("Número de les pòlisses que han donat error (REVISAR)\n").format(block_name)  # noqa: E501
            error_names = self.get_names(cursor, uid, errors, namespace, context)
            summary += ", ".join(str(error) for error in error_names)
            summary += "  " + self.get_names_as_link(cursor, uid, errors, namespace, "Errors (no han canviat d'estat)", context)  # noqa: E501
            summary += _("\n\n")

        if reviews:
            if namespace == 'atc':
                summary += _("Id's de {} que han passat a estat 'Revisar'\n").format(block_name)
            else:
                summary += _("Número de les pòlisses que han passat a estat 'Revisar'\n").format(block_name)  # noqa: E501
            review_names = self.get_names(cursor, uid, reviews, namespace, context)
            summary += ", ".join(str(review) for review in review_names)
            summary += "  " + self.get_names_as_link(cursor, uid, reviews, namespace, "Per Revisar", context)  # noqa: E501
            summary += _("\n\n")

        return updated, not_updated, errors, msg, summary

    def update_item_if_possible(self, cursor, uid, item_id, namespace, context=None):
        context = self._ensure_updater_config_context(cursor, uid, context)

        item_obj = self.pool.get(_namespaces[namespace]['model'])
        history_obj = self.pool.get(_namespaces[namespace]['history_model'])
        state_obj = self.pool.get("som.autoreclama.state")
        cond_obj = self.pool.get("som.autoreclama.state.condition")
        item_data = item_obj.get_autoreclama_data(cursor, uid, item_id, namespace, context)

        autoreclama_state = _namespaces[namespace]['state_field']
        state = item_obj.read(cursor, uid, item_id, [autoreclama_state], context)
        if autoreclama_state in state and state[autoreclama_state]:
            autoreclama_state_id = state[autoreclama_state][0]
        else:
            return False, None, _(u"Sense estat d'autoreclama inicial")

        cond_ids = self._get_condition_ids(
            cursor, uid, autoreclama_state_id, namespace, context
        )

        do_not_execute = context and context.get("search_only", False)
        for cond_id in cond_ids:
            cond_data = self._get_condition_data(cursor, uid, cond_id, context)
            if cond_obj.fit_condition_data(cond_data, item_data, namespace):
                if do_not_execute:
                    return True, None, _(u"Testing")

                next_state_id = cond_data["next_state_id"][0]
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
        context = self._ensure_updater_config_context(cursor, uid, context)

        atc_ids = self.get_atc_candidates_to_update(cursor, uid, context)
        a, b, c, atc_msg, atc_sum = self.update_items_if_possible(
            cursor, uid, atc_ids, "atc", False, context)

        pol_ids = self.get_polissa_candidates_to_update(cursor, uid, "polissa", context)
        a, b, c, pol006_msg, pol006_sum = self.update_items_if_possible(
            cursor, uid, pol_ids, "polissa", False, context)

        pol_ids = self.get_polissa_candidates_to_update(cursor, uid, "polissa009", context)
        a, b, c, pol009_msg, pol009_sum = self.update_items_if_possible(
            cursor, uid, pol_ids, "polissa009", False, context)

        return "\n\n".join([atc_sum, pol006_sum, pol009_sum, atc_msg, pol006_msg, pol009_msg])

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
